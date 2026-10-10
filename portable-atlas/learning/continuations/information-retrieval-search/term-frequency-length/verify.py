"""Atlas: saved score verification using fixed rational hand expectations, without importing producer."""
import argparse,copy,hashlib,json,math
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def need(x,label):
 if not x:raise ValueError(label)
def near(a,b,label):need(type(a) in (int,float) and math.isfinite(a) and abs(a-float(b))<=1e-12,label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(data):
 oracle=json.loads((ROOT/'hand-oracle.json').read_text());fixture=json.loads((ROOT/'fixtures.json').read_text())
 need(data['status']=='observed' and data['search_engine_executed'] is False and data['user_relevance_evaluated'] is False,'calculation classification')
 need(data['priority_observed']==10,'priority')
 need(data['fixture_sha256']==sha(ROOT/'fixtures.json'),'fixture binding')
 need([x['mode_id'] for x in data['cases']]==[x['id'] for x in oracle['cases']],'case set/order')
 for actual,expected in zip(data['cases'],oracle['cases']):
  for k in ['N','df','total_tokens','match_ids','nonmatch_ids']:need(actual[k]==oracle[k],k)
  near(actual['avgdl'],Fraction(oracle['avgdl']),'avgdl');need(actual['idf_variant']=='ln(N/df)','IDF variant');near(actual['idf'],math.log(2),'IDF')
  need(actual['query']=='alpha','query');need(actual['idf']>0,'common positive IDF')
  for k in ['matched_order','tie_groups']:need(actual[k]==expected[k],k)
  need(actual['k1']==(None if expected['id']=='raw-tfidf' else 1),'k1')
  need(actual['b']=={'raw-tfidf':None,'bm25-b0':0,'bm25-bhalf':.5,'bm25-b1':1}[expected['id']],'b')
  need(len(actual['rows'])==4,'row count')
  for row,hand,counts in zip(actual['rows'],expected['rows'],oracle['document_counts']):
   for k in ['id','length','term_frequency','positions']:need(row[k]==counts[k],k)
   need(row['tokens']==next(d['text'].split(' ') if d['text'] else [] for d in fixture['documents'] if d['id']==row['id']),'tokens')
   matching=counts['term_frequency']>0;need(row['matched'] is matching and row['nonmatch_short_circuit'] is (not matching),'candidate/empty short circuit')
   need(row['rank']==hand['rank'],'display rank')
   f=Fraction(hand['coefficient']);near(row['coefficient'],f,'coefficient');near(row['score'],float(f)*math.log(2),'score')
   if matching:
    need(Fraction(row['numerator'])==Fraction(hand['numerator']),'numerator')
    need(Fraction(row['denominator'])==Fraction(hand['denominator']),'denominator')
    need(Fraction(hand['numerator'])/Fraction(hand['denominator'])==f,'hand arithmetic')
   else:need(row['numerator'] is None and row['denominator'] is None and row['score']==0 and row['rank'] is None,'nonmatch not ranked')
 expected_errors={'extra_root_key':'input_keys','bool_schema':'schema','duplicate_document':'duplicate_document_id','non_ascii':'document_tokens','uppercase':'document_tokens','double_space':'document_tokens','empty_query':'single_query_token','multiple_query_tokens':'single_query_token','unmatched_query':'query_not_in_corpus','all_empty_documents':'empty_corpus','bool_parameter':'fixed_mode_contract','changed_parameter':'fixed_mode_contract','unknown_mode':'unknown_mode'}
 need(len(data['input_refusals'])==len(expected_errors),'input refusal count')
 need({r['case']:r['code'] for r in data['input_refusals']}==expected_errors,'input refusal codes')
 need(all(r['classification']=='expected_input_refusal' and r['exception']=='ValueError' for r in data['input_refusals']),'refusal class')
 return True

def verify(run):
 run=run.resolve();need(run.parent==ROOT/'observations','owned run');r=json.loads((run/'report.json').read_text());need(r['status']=='observed' and r['child_reaped'] and r['output_complete'] and r['exit_code']==0 and not r['timed_out'],'child completion')
 need(sha(ROOT/r['resource_gate_file'])==r['resource_gate_sha256'] and 0<=r['resource_gate_age_seconds']<=60,'resource gate binding')
 need(r['priority_guard']['ready'] and r['priority_guard']['observed_nice']==10,'priority guard')
 for n,h in r['sources'].items():need(sha(ROOT/n)==h,'source binding: '+n)
 for stem in ['stdout','stderr','result']:need(sha(run/r[stem+'_file'])==r[stem+'_sha256'],'saved file binding '+stem)
 data=json.loads((run/r['stdout_file']).read_text());need(data==json.loads((run/r['result_file']).read_text()),'stdout/result');check(data)
 changed=[]
 mutations=[('missing_case',lambda x:x['cases'].pop()),('changed_IDF',lambda x:x['cases'][0].update(idf=0,idf_variant='probabilistic')),
 ('changed_avgdl',lambda x:x['cases'][1].update(avgdl=16/3)),('wrong_coefficient',lambda x:x['cases'][1]['rows'][0].update(coefficient=2.0)),
 ('nonmatch_ranked',lambda x:x['cases'][3]['rows'][2].update(rank=3)),('tie_hidden',lambda x:x['cases'][2].update(tie_groups=[])),
 ('tie_input_order',lambda x:x['cases'][2].update(matched_order=['d2','d1'])),('stale_mode',lambda x:x['cases'].__setitem__(3,copy.deepcopy(x['cases'][0]))),
 ('wrong_term_count',lambda x:x['cases'][0]['rows'][0].update(term_frequency=1)),('zero_division_branch',lambda x:x['cases'][3]['rows'][2].update(denominator=0.0))]
 for label,mutate in mutations:
  altered=copy.deepcopy(data);mutate(altered)
  try:check(altered)
  except (ValueError,KeyError,IndexError,TypeError):changed.append(label)
  else:raise ValueError('missed alteration '+label)
 return {'title':'Atlas 保存計算の独立照合','passed':True,'cases':4,'document_rows':16,'input_refusals':13,'altered_results_detected':changed,'producer_imported':False,'model_executed':False,'run':str(run.relative_to(ROOT))}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);a=p.parse_args();print(json.dumps(verify(ROOT/a.run),ensure_ascii=False,indent=2))

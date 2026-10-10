"""Atlas: compare saved results to fixed rational products; never import the producer."""
import argparse,copy,hashlib,json,math
from decimal import Decimal,localcontext
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,label):
 if not ok:raise ValueError(label)
def log_fraction(text):
 f=Fraction(text)
 with localcontext() as c:c.prec=50;return (Decimal(f.numerator)/Decimal(f.denominator)).ln()
def near(value,expected,label):need(type(value) in [float,int] and math.isfinite(value) and abs(Decimal(str(value))-Decimal(expected))<=Decimal('1e-12'),label)
def check(data):
 hand=json.loads((ROOT/'hand-oracle.json').read_text());fixture=json.loads((ROOT/'fixtures.json').read_text());queries={q['id']:q['query'] for q in fixture['queries']}
 need(data['status']=='observed' and data['priority_observed']==10 and data['fixture_sha256']==sha(ROOT/'fixtures.json'),'execution header')
 need(data['search_engine_executed'] is False and data['user_relevance_evaluated'] is False,'scope')
 need([c['request_id'] for c in data['cases']]==[q['id'] for q in fixture['queries']],'request identity and order')
 for actual,expected in zip(data['cases'][:5],hand['query_cases']):
  need(actual['request_id']==expected['id'] and actual['query']==queries[expected['id']] and actual['query_tokens']==queries[expected['id']].split(' '),'original request')
  for k in ['canonical_terms','removed_duplicates','matches','weighted_order','weighted_ties','unit_order','unit_ties']:need(actual[k]==expected[k],k)
  need(actual['status']=='calculated' and actual['N']==4 and actual['avgdl']==4 and actual['total_tokens']==16 and actual['k1']==1 and actual['b']==0 and actual['idf_variant']=='ln(N/df)','fixed statistics')
  terms=expected['canonical_terms'];need(set(actual['df'])==set(terms) and set(actual['idf'])==set(terms),'term keys')
  for term in terms:need(actual['df'][term]==hand['terms'][term]['df'],'document frequency');near(actual['idf'][term],log_fraction(hand['terms'][term]['idf_log_argument']),'IDF')
  need(len(actual['rows'])==4,'row count');exact_products=[]
  for i,(row,counts) in enumerate(zip(actual['rows'],hand['document_counts'])):
   need(row['id']==counts['id'] and row['length']==4,'document identity');need(row['tokens']==next(d['text'].split(' ') for d in fixture['documents'] if d['id']==row['id']),'tokens')
   need([c['term'] for c in row['contributions']]==terms,'contribution terms');product=Fraction(1);units=0
   for contribution in row['contributions']:
    term=contribution['term'];positions=counts[term+'_positions'];matched=bool(positions);need(contribution['positions']==positions and contribution['tf']==len(positions) and contribution['df']==hand['terms'][term]['df'],'term counts')
    near(contribution['idf'],log_fraction(hand['terms'][term]['idf_log_argument']),'term IDF');need(contribution['tf_factor']==int(matched) and contribution['unit_contribution']==int(matched) and contribution['nonmatch_short_circuit'] is (not matched),'fixed TF factor')
    near(contribution['weighted_contribution'],log_fraction(hand['terms'][term]['idf_log_argument']) if matched else Decimal(0),'weighted contribution')
    if matched:product*=Fraction(hand['terms'][term]['idf_log_argument']);units+=1
   need(product==Fraction(expected['products'][i]) and units==expected['unit_scores'][i],'independent product/units');exact_products.append(product)
   near(row['weighted_score'],log_fraction(expected['products'][i]),'weighted total');near(row['unit_score'],Decimal(units),'unit total');need(row['matched'] is (row['id'] in expected['matches']),'candidate')
   for name in ['weighted','unit']:need(row[name+'_rank']==(expected[name+'_order'].index(row['id'])+1 if row['matched'] else None),'display rank')
  by_id=dict(zip(hand['document_order'],exact_products));need(sorted(expected['matches'],key=lambda id:(-by_id[id],id))==expected['weighted_order'],'exact rational order')
 refused=data['cases'][5];h=hand['expected_refusal'];need(refused=={'request_id':h['id'],'query':h['query'],'status':'expected_query_refusal','code':h['code'],'missing_terms':h['missing_terms'],'rows':None,'scores_returned':False},'whole unknown-query refusal')
 codes={'extra_key':'input_keys','bool_schema':'schema','bool_parameter':'fixed_parameters','changed_parameter':'fixed_parameters','duplicate_id':'duplicate_document_id','empty_document':'document_tokens','wrong_length':'fixed_document_length','changed_frequency':'fixed_frequency','empty_query':'query_tokens','uppercase_query':'query_tokens','double_space':'query_tokens','too_many_terms':'query_tokens','filler_query':'query_outside_lesson'}
 need(len(data['input_refusals'])==13 and {r['case']:r['code'] for r in data['input_refusals']}==codes,'input refusals');need(all(r['classification']=='expected_input_refusal' and r['scores_returned'] is False for r in data['input_refusals']),'refusal scope')
 return True
def verify(run):
 run=run.resolve();need(run.parent==ROOT/'observations','owned run');r=json.loads((run/'report.json').read_text());need(r['status']=='observed' and r['child_reaped'] and r['output_complete'] and r['exit_code']==0 and not r['timed_out'],'child completion');need(r['priority_guard']['ready'] and r['priority_guard']['observed_nice']==10,'actual nice')
 need(sha(ROOT/r['resource_gate_file'])==r['resource_gate_sha256'] and 0<=r['resource_gate_age_seconds']<=60,'fresh resources')
 for name,h in r['sources'].items():need(sha(ROOT/name)==h,'source: '+name)
 for stem in ['stdout','stderr','result']:need(sha(run/r[stem+'_file'])==r[stem+'_sha256'],'saved '+stem)
 d=json.loads((run/r['result_file']).read_text());need(d==json.loads((run/r['stdout_file']).read_text()),'stdout/result');check(d)
 edits=[('wrong_request',lambda d:d['cases'][3].update(query='alpha beta')),('repeat_counted',lambda d:d['cases'][4].update(removed_duplicates=0)),('wrong_df',lambda d:d['cases'][2]['df'].update(beta=3)),('wrong_IDF_variant',lambda d:d['cases'][2].update(idf_variant='probabilistic')),('missing_term',lambda d:d['cases'][2]['rows'][2]['contributions'].pop()),('wrong_contribution',lambda d:d['cases'][2]['rows'][2]['contributions'][1].update(weighted_contribution=0)),('wrong_total',lambda d:d['cases'][2]['rows'][2].update(weighted_score=2)),('tie_hidden',lambda d:d['cases'][2].update(weighted_ties=[])),('wrong_order',lambda d:d['cases'][2].update(weighted_order=['d3','d1','d2','d4'])),('nonmatch_ranked',lambda d:d['cases'][0]['rows'][1].update(weighted_rank=4)),('unknown_silently_dropped',lambda d:d['cases'][5].update(rows=[])),('missing_case',lambda d:d['cases'].pop())];detected=[]
 for name,change in edits:
  altered=copy.deepcopy(d);change(altered)
  try:check(altered)
  except (ValueError,KeyError,IndexError,TypeError):detected.append(name)
  else:raise ValueError('missed mutation '+name)
 return {'title':'Atlas independent saved-result verification','passed':True,'successful_queries':5,'document_rows':20,'term_contributions':32,'expected_unknown_query_refusals':1,'other_input_refusals':13,'mutations_detected':detected,'producer_imported':False,'model_executed':False,'run':str(run.relative_to(ROOT))}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);a=p.parse_args();print(json.dumps(verify(ROOT/a.run),ensure_ascii=False,indent=2))

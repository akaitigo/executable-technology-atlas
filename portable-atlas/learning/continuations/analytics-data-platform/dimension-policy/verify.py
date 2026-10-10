"""Atlas: read saved SQLite results against fixed hand expectations; never execute SQL."""
import argparse,copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(r,o):
 assert r['status']=='observed' and r['priority_observed']==10
 assert r['cleanup']=={'opened':5,'closed':5,'complete':True}
 assert r['browser_executed'] is False and r['persistent_database_opened'] is False and r['publication_performed'] is False
 assert len(r['policies'])==3 and len(r['foreign_key_probes'])==2
 for actual,expected in zip(r['policies'],o['policies']):
  for k,v in expected.items():assert actual[k]==v,(expected['policy'],k)
  for k in ['candidate_ids','classification_rows','unknown_ids','null_key_ids']:assert actual[k]==o[k],k
  assert actual['foreign_keys_readback']==1 and actual['database']==':memory:' and actual['publish_performed'] is False
  assert actual['source_id']
  decisions=[[i,'accepted' if i in expected['accepted_ids'] else 'quarantined' if i in expected['quarantined_ids'] else 'rejected',int(i in expected['metric_ids'])] for i in o['input_ids']]
  assert actual['decisions']==decisions
  assert actual['quarantine_records']==[[i,'unknown_customer_key'] for i in expected['quarantined_ids']]
  assert actual['rejection_records']==[[i,'batch_rejected_unknown_key'] for i in expected['rejected_ids']]
 for actual,expected in zip(r['foreign_key_probes'],o['foreign_key_probes']):
  for k,v in expected.items():assert actual[k]==v,('fk',k)
  assert actual['pragma_in_transaction'] is False and actual['isolation_level'] is None and actual['database']==':memory:'
  assert 'order_id INTEGER PRIMARY KEY' in actual['schema_sql'] and 'REFERENCES customers(customer_id)' in actual['schema_sql']
  assert actual['rowid_order_id_pairs']==[[i,i] for i in expected['saved_ids']]
  assert len(actual['events'])==6
  for i,event in enumerate(actual['events']):
   assert event['order_id']==i+1 and event['customer_id']==[10,10,999,None,20,20][i]
   assert event['outcome']==expected['outcomes'][i] and event['saved_ids']==expected['ids_after_each'][i]
   assert event['in_transaction_before'] is False and event['in_transaction_after'] is False
   if event['outcome']=='inserted':assert event['error'] is None
   else:assert event['error']['type']=='IntegrityError' and 'FOREIGN KEY constraint failed' in event['error']['message']
 assert r['foreign_key_probes'][0]['schema_sql']==r['foreign_key_probes'][1]['schema_sql']
 refusals=[('extra_key','input_keys'),('bool_schema','schema'),('wrong_policy','policies'),('null_policy','null_policy'),('metric','metric'),('missing_order','orders_count'),('bad_shape','orders_shape'),('bool_id','orders_id'),('duplicate_order','orders_duplicate'),('bool_amount','amount'),('text_customer','customer_key'),('orphan_line','line_order')]
 assert r['input_refusals']==[{'case':n,'status':'expected_refusal','reason':c} for n,c in refusals]
 return True
def mutations(r,o):
 edits=[('lost_order',lambda z:z['policies'][2]['accepted_ids'].pop()),('unknown_as_null',lambda z:z['policies'][2]['classification_rows'][2].__setitem__(1,'null_key')),('reject_as_zero',lambda z:z['policies'][0].__setitem__('sum_amount',0)),('wrong_denominator',lambda z:z['policies'][1]['missing_fraction'].__setitem__('denominator',5)),('line_fanout',lambda z:z['policies'][2].__setitem__('sum_amount',380)),('null_key_quarantined',lambda z:z['policies'][1]['quarantined_ids'].append(4)),('rejected_publish',lambda z:z['policies'][0].__setitem__('publish_performed',True)),('fk_unknown_accepted',lambda z:z['foreign_key_probes'][1]['outcomes'].__setitem__(2,'inserted')),('old_ids_after_failure',lambda z:z['foreign_key_probes'][1]['ids_after_each'].__setitem__(2,[1,2,3])),('false_null_rejection',lambda z:z['foreign_key_probes'][1]['events'][3].__setitem__('outcome','foreign_key_constraint')),('lost_violation',lambda z:z['foreign_key_probes'][0].__setitem__('violations',[])),('cleanup_incomplete',lambda z:z['cleanup'].__setitem__('closed',4))]
 out=[]
 for name,edit in edits:
  z=copy.deepcopy(r);edit(z)
  try:check(z,o)
  except (AssertionError,KeyError,TypeError,IndexError):out.append({'case':name,'detected':True})
  else:raise AssertionError('undetected modification: '+name)
 return out
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);p.add_argument('--save',action='store_true');a=p.parse_args();d=ROOT/a.run;r=json.loads((d/'result.json').read_text());report=json.loads((d/'report.json').read_text());o=json.loads((ROOT/'hand-oracle.json').read_text())
 check(r,o);assert r['fixture_sha256']==sha(ROOT/'fixtures.json');assert report['status']=='observed' and report['child_reaped'] is True and report['exit_code']==0
 assert json.loads((d/'stdout.txt').read_text())==r
 for n,h in report['sources'].items():assert sha(ROOT/n)==h,n
 for n in ['stdout','stderr']:assert sha(d/(n+'.txt'))==report[n+'_sha256']
 assert report['result_sha256']==sha(d/'result.json');assert report['priority_guard']['observed_nice']==10 and report['priority_guard']['ready'] is True
 assert sha(ROOT/report['resource_gate_file'])==report['resource_gate_sha256']
 x={'title':'Atlas saved SQLite result verification','passed':True,'policy_count':3,'policy_row_decisions':18,'foreign_key_insert_events':12,'input_refusals':12,'mutation_checks':mutations(r,o),'source_files':len(report['sources']),'result_sha256':sha(d/'result.json'),'sqlite_reexecuted':False,'browser_executed':False}
 if a.save:(ROOT/'observations/calculation-verification.json').write_text(json.dumps(x,indent=2)+'\n')
 print(json.dumps(x))
if __name__=='__main__':main()

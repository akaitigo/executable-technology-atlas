"""Atlas: one short actual SQLite batch; complete saved outcomes and cleanup."""
import copy,datetime,hashlib,json,os,platform,sqlite3,sys
from pathlib import Path
from model import validate,policy_case,fk_probe,Refusal
ROOT=Path(__file__).resolve().parent
def main():
 x=json.loads((ROOT/'fixtures.json').read_text());q=json.loads((ROOT/'queries.json').read_text());cleanup={'opened':0,'closed':0};result={'title':'Atlas SQLite dimension policy observations','status':'preparing','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'priority_observed':os.getpriority(os.PRIO_PROCESS,0),'fixture_sha256':hashlib.sha256((ROOT/'fixtures.json').read_bytes()).hexdigest(),'runtime':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'system':platform.system(),'architecture':platform.machine()},'policies':[],'foreign_key_probes':[],'input_refusals':[],'cleanup':cleanup,'browser_executed':False,'persistent_database_opened':False,'publication_performed':False}
 try:
  assert result['priority_observed']==10,'actual nice 10 required'
  for p in x['policies']:result['policies'].append(policy_case(x,q,p,cleanup))
  for n in [0,1]:result['foreign_key_probes'].append(fk_probe(x,q,n,cleanup))
  changes=[('extra_key','input_keys',lambda z:z.update(extra=1)),('bool_schema','schema',lambda z:z.update(schema=True)),('wrong_policy','policies',lambda z:z.update(policies=['retain'])),('null_policy','null_policy',lambda z:z.update(null_customer_policy='reject')),('metric','metric',lambda z:z.update(metric='count_lines')),('missing_order','orders_count',lambda z:z['orders'].pop()),('bad_shape','orders_shape',lambda z:z['orders'][0].pop()),('bool_id','orders_id',lambda z:z['orders'][0].__setitem__(0,True)),('duplicate_order','orders_duplicate',lambda z:z['orders'][1].__setitem__(0,1)),('bool_amount','amount',lambda z:z['orders'][0].__setitem__(2,True)),('text_customer','customer_key',lambda z:z['orders'][0].__setitem__(1,'10')),('orphan_line','line_order',lambda z:z['lines'][0].__setitem__(1,999))]
  for name,code,change in changes:
   z=copy.deepcopy(x);change(z)
   try:validate(z)
   except Refusal as e:
    assert str(e)==code;result['input_refusals'].append({'case':name,'status':'expected_refusal','reason':str(e)})
   else:raise AssertionError('invalid fixture accepted: '+name)
  assert cleanup=={'opened':5,'closed':5};result['status']='observed'
 except Exception as e:result.update(status='execution_failed',error={'type':type(e).__name__,'message':str(e)})
 finally:
  cleanup['complete']=cleanup['opened']==cleanup['closed'];print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
 return 0 if result['status']=='observed' else 1
if __name__=='__main__':sys.exit(main())

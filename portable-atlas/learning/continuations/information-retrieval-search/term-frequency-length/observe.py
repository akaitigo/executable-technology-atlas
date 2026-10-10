"""Atlas: produce four finite score calculations and expected input refusals."""
import copy,datetime,hashlib,json,os,platform,sys,time
from pathlib import Path
from model import calculate
ROOT=Path(__file__).resolve().parent

def main():
 priority=os.getpriority(os.PRIO_PROCESS,0)
 if priority!=10:raise RuntimeError('Atlas: nice 10 must be verified before calculation')
 start=time.monotonic();fixture=json.loads((ROOT/'fixtures.json').read_text());cases=[calculate(fixture,m['id']) for m in fixture['modes']]
 refusals=[]
 changes=[
 ('extra_root_key',lambda x:x.update(extra=1)),
 ('bool_schema',lambda x:x.update(schema=True)),
 ('duplicate_document',lambda x:x['documents'][0].update(id='d1')),
 ('non_ascii',lambda x:x['documents'][0].update(text='日本語')),
 ('uppercase',lambda x:x['documents'][0].update(text='Alpha x')),
 ('double_space',lambda x:x['documents'][0].update(text='alpha  x')),
 ('empty_query',lambda x:x.update(query='')),
 ('multiple_query_tokens',lambda x:x.update(query='alpha x')),
 ('unmatched_query',lambda x:x.update(query='absent')),
 ('all_empty_documents',lambda x:[d.update(text='') for d in x['documents']]),
 ('bool_parameter',lambda x:x['modes'][1].update(k1=True)),
 ('changed_parameter',lambda x:x['modes'][3].update(b='0.5'))]
 for label,mutation in changes:
  data=copy.deepcopy(fixture);mutation(data)
  try:calculate(data,'raw-tfidf')
  except ValueError as e:refusals.append({'case':label,'exception':'ValueError','code':str(e),'classification':'expected_input_refusal'})
  else:raise RuntimeError('expected refusal absent: '+label)
 try:calculate(fixture,'unknown-mode')
 except ValueError as e:refusals.append({'case':'unknown_mode','exception':'ValueError','code':str(e),'classification':'expected_input_refusal'})
 else:raise RuntimeError('unknown mode not refused')
 result={'title':'Atlas 語の頻度と文書長の保存計算','schema':1,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':{'implementation':platform.python_implementation(),'python':platform.python_version(),'system':platform.system(),'machine':platform.machine()},'priority_observed':priority,'fixture_sha256':hashlib.sha256((ROOT/'fixtures.json').read_bytes()).hexdigest(),'cases':cases,'input_refusals':refusals,'calculation_elapsed_seconds':time.monotonic()-start,'search_engine_executed':False,'user_relevance_evaluated':False,'status':'observed'}
 print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))

if __name__=='__main__':main()

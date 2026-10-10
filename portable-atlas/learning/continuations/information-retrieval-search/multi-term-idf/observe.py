"""Atlas: record one small multi-term calculation batch after actual priority guard."""
import copy,datetime,hashlib,json,os,platform,time
from pathlib import Path
from model import calculate,InputError
ROOT=Path(__file__).resolve().parent
def main():
 priority=os.getpriority(os.PRIO_PROCESS,0)
 if priority!=10:raise RuntimeError('Atlas actual nice 10 required')
 data=json.loads((ROOT/'fixtures.json').read_text());start=time.monotonic();cases=[]
 for q in data['queries']:
  try:cases.append(calculate(data,q['id'],q['query']))
  except InputError as e:
   if q['id']!='unknown-term' or e.code!='unknown_query_term':raise
   cases.append({'request_id':q['id'],'query':q['query'],'status':'expected_query_refusal','code':e.code,**e.details,'rows':None,'scores_returned':False})
 refusals=[]
 tests=[('extra_key',lambda d:d.update(extra=True),'alpha','input_keys'),('bool_schema',lambda d:d.update(schema=True),'alpha','schema'),('bool_parameter',lambda d:d['parameters'].update(k1=True),'alpha','fixed_parameters'),('changed_parameter',lambda d:d['parameters'].update(b=1),'alpha','fixed_parameters'),('duplicate_id',lambda d:d['documents'][0].update(id='d2'),'alpha','duplicate_document_id'),('empty_document',lambda d:d['documents'][0].update(text=''),'alpha','document_tokens'),('wrong_length',lambda d:d['documents'][0].update(text='alpha x'),'alpha','fixed_document_length'),('changed_frequency',lambda d:d['documents'][0].update(text='alpha alpha x x'),'alpha','fixed_frequency'),('empty_query',lambda d:None,'','query_tokens'),('uppercase_query',lambda d:None,'Alpha','query_tokens'),('double_space',lambda d:None,'alpha  beta','query_tokens'),('too_many_terms',lambda d:None,'alpha beta alpha beta','query_tokens'),('filler_query',lambda d:None,'x','query_outside_lesson')]
 for label,mutate,query,code in tests:
  changed=copy.deepcopy(data);mutate(changed)
  try:calculate(changed,'input-check',query)
  except InputError as e:
   if e.code!=code:raise RuntimeError(label+': unexpected refusal '+e.code)
   refusals.append({'case':label,'code':e.code,'classification':'expected_input_refusal','scores_returned':False})
  else:raise RuntimeError(label+': input unexpectedly accepted')
 return {'title':'Atlas multi-term saved calculation','schema':1,'status':'observed','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':{'python':platform.python_version(),'implementation':platform.python_implementation(),'system':platform.system(),'machine':platform.machine()},'priority_observed':priority,'fixture_sha256':hashlib.sha256((ROOT/'fixtures.json').read_bytes()).hexdigest(),'cases':cases,'input_refusals':refusals,'calculation_elapsed_seconds':time.monotonic()-start,'search_engine_executed':False,'user_relevance_evaluated':False}
if __name__=='__main__':print(json.dumps(main(),ensure_ascii=False,indent=2))

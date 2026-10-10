import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
TASK='sum-demo-v1'
class Refused(Exception):pass
def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def read_json(name,trace):
 trace.append({'event':'json-read','fixture':name})
 try:b=(ROOT/'fixtures'/name).read_bytes()
 except OSError:raise OSError('fixture-read-failed') from None
 try:return json.loads(b),sha(b)
 except json.JSONDecodeError:raise Refused('json-syntax')
def resolve(manifest,interval,selector,mode,trace):
 if interval not in manifest['versions']:raise Refused('unknown-interval')
 if selector!='latest' and selector not in manifest['versions'][interval]:raise Refused('unknown-version')
 selected=manifest['latest'][interval] if selector=='latest' or mode=='latest-lookup' else selector
 if selected not in manifest['versions'][interval]:raise Refused('unknown-version')
 fixture=manifest['versions'][interval][selected];values,raw_sha=read_json(fixture,trace)
 if type(values) is not list or not values or any(type(x) is not int or not 0<=x<=100 for x in values):raise Refused('integer-list-contract')
 result={'version_label':selected,'fixture':fixture,'values':values,'input_sha':sha(encoded(values)),'raw_file_sha':raw_sha}
 trace.append({'event':'resolved-input','interval':interval,'requested':selector,'selected':selected,'input_sha':result['input_sha']});return result
def key(interval,digest,mode):
 return [TASK,digest] if mode=='drop-interval' else [TASK,interval] if mode=='drop-digest' else [TASK,interval,digest]
def artifact(interval,resolved):
 body={'binding':{'task':TASK,'interval':interval,'input_sha':resolved['input_sha']},'value':sum(resolved['values']),'count':len(resolved['values'])}
 return {'body':body,'artifact_sha':sha(encoded(body))}
def run(spec,mode):
 trace=[];cache={};initial_manifest,_=read_json('manifest-before.json',trace)
 if spec['seed']:
  initial=resolve(initial_manifest,'day1','v1','normal',trace);k=key('day1',initial['input_sha'],mode);cache[tuple(k)]=artifact('day1',initial);trace.append({'event':'seed-cache','key':k,'value':5})
 if spec.get('corrupt_cache'):
  next(iter(cache.values()))['body']['value']=999;trace.append({'event':'corrupt-cached-body','artifact_sha_retained':True})
 before=json.loads(json.dumps(list(cache.values())));resolved=None;k=None;hit=None;value=None;used=None;matches=None;status='success';reason=None;calls=0
 try:
  manifest,_=read_json(spec['manifest'],trace);resolved=resolve(manifest,spec['interval'],spec['selector'],mode,trace);k=key(spec['interval'],resolved['input_sha'],mode)
  hit=tuple(k) in cache;trace.append({'event':'cache-lookup','key':k,'hit':hit})
  expected_binding={'task':TASK,'interval':spec['interval'],'input_sha':resolved['input_sha']}
  if hit:
   used=cache[tuple(k)]
   if sha(encoded(used['body']))!=used['artifact_sha']:raise Refused('cached-content-digest')
   matches=used['body']['binding']==expected_binding
   if mode in ['normal','latest-lookup'] and not matches:raise Refused('cached-request-binding')
   value=used['body']['value'];trace.append({'event':'cache-reuse','value':value,'binding_matches_request':matches})
  else:
   calls+=1;used=artifact(spec['interval'],resolved);cache[tuple(k)]=used;matches=True;value=used['body']['value'];trace.append({'event':'task-compute','value':value,'calls':calls})
 except Refused as e:status='expected-refusal';reason=str(e);value=None;trace.append({'event':'refused','reason':reason})
 except OSError as e:status='execution-error';reason=str(e);value=None;trace.append({'event':'execution-error','reason':reason})
 return {'status':status,'request':{'interval':spec['interval'],'selector':spec['selector']},'resolved_input':resolved,'cache_key':k,'cache_hit':hit,'value':value,'task_calls':calls,'reused_binding_matches_request':matches,'artifact':used if status=='success' else None,'reason':reason,'cache_before':before,'cache_after':list(cache.values()),'trace':trace}
def main():
 specs=json.loads((ROOT/'contracts.json').read_text())['cases'];modes=['normal','drop-interval','drop-digest','latest-lookup']
 print(json.dumps({'rows':[{'id':s['id'],'modes':{m:run(s,m) for m in modes}} for s in specs]},ensure_ascii=False))
if __name__=='__main__':main()

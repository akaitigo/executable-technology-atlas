"""Validate finite input and budget measured bytes; no ResourceTiming simulation."""
import json,copy,uuid,http.client,gzip,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIXTURE=json.loads((ROOT/'fixture.json').read_text())
PLAIN=b'abc';GZIP=bytes.fromhex('1f8b08000000000000034b4c4a0600c241243503000000')
class Refused(Exception):pass
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def resolve(case,input_json=None):
 c=next((copy.deepcopy(c) for c in FIXTURE['cases'] if c['id']==case),None)
 if c is None:raise Refused('UNKNOWN_CASE')
 if input_json:
  try:x=json.loads(input_json)
  except ValueError:raise Refused('INPUT_JSON')
  if not isinstance(x,dict) or set(x)!= {'encoding','budget','policy','variant'}:raise Refused('INPUT_FIELDS')
  c.update(x)
 if type(c['budget']) is not int or not 0<=c['budget']<=23:raise Refused('BUDGET')
 if c['encoding'] not in ['plain','gzip']:raise Refused('ENCODING')
 if c['policy'] not in ['encoded','decoded-fault']:raise Refused('POLICY')
 if c['variant'] not in ['normal','timing-missing','http-failure']:raise Refused('VARIANT')
 return c
def empty(case,status,reason,input=None):return dict(case=case,input=input,status=status,reason=reason,measurement=None,used=None,accepted=None)
def prepare(case,input_json=None):
 try:
  c=resolve(case,input_json);id=uuid.uuid4().hex;path='/body/'+('error' if c['variant']=='http-failure' else c['encoding'])+'?request='+id
  return dict(case=case,input=c,status='READY',reason='',body_path=path,request_id=id)
 except Refused as e:return empty(case,'INPUT_REFUSED',str(e))
def decide(c,m):
 if not isinstance(m,dict) or set(m)!= {'encoded','decoded'} or any(type(m[k]) is not int or m[k]<=0 for k in ['encoded','decoded']):return empty(c['id'],'UNSUPPORTED_TIMING','TIMING_SIZE_UNAVAILABLE',c)
 if m['encoded']!=(3 if c['encoding']=='plain' else 23) or m['decoded']!=3:return empty(c['id'],'UNSUPPORTED_TIMING','BODY_SIZE_MISMATCH',c)
 used=m['encoded'] if c['policy']=='encoded' else m['decoded']
 return dict(case=c['id'],input=c,status='NORMAL' if c['policy']=='encoded' else 'FAULT_DECODED_BUDGET',reason='',measurement=m,used=used,accepted=used<=c['budget'])
def run(case,port=None,input_json=None):
 plan=prepare(case,input_json)
 if plan['status']!='READY':return dict(result=plan,wire=None)
 c=plan['input']
 if type(port) is not int or not 1<=port<=65535:return dict(result=empty(case,'UNSUPPORTED_LIVE_PORT','OWNED_PORT_REQUIRED',c),wire=None)
 conn=http.client.HTTPConnection('127.0.0.1',port,timeout=5);start=utc()
 try:
  conn.request('GET',plan['body_path'],headers={'Accept-Encoding':c['encoding'] if c['encoding']=='gzip' else 'identity','Cache-Control':'no-store'});resp=conn.getresponse();body=resp.read();headers={k.lower():v for k,v in resp.getheaders()};wire=dict(path=plan['body_path'],request_id=plan['request_id'],started_utc=start,ended_utc=utc(),http_status=resp.status,headers=headers,body_hex=body.hex(),body_bytes=len(body),decoded_hex=None,decoded_bytes=None,source='actual http.client raw response; no Browser ResourceTiming')
  if resp.status!=200:return dict(result=empty(case,'EXECUTION_FAILURE','HTTP_'+str(resp.status),c),wire=wire)
  decoded=gzip.decompress(body) if headers.get('content-encoding')=='gzip' else body;wire.update(decoded_hex=decoded.hex(),decoded_bytes=len(decoded))
  if c['variant']=='timing-missing':result=empty(case,'BROWSER_REQUIRED','TIMING_LOOKUP_MUST_BE_OBSERVED_IN_BROWSER',c)
  else:result=decide(c,dict(encoded=len(body),decoded=len(decoded)))
  return dict(result=result,wire=wire)
 except Exception as e:return dict(result=empty(case,'EXECUTION_FAILURE',type(e).__name__+': '+str(e),c),wire=None)
 finally:conn.close()

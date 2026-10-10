# SPDX-License-Identifier: Apache-2.0
import json
def sender_domain(fixture_id,delay_ms):return dict(fixture_id=fixture_id,delay_ms=delay_ms)
def serialize(domain,mode):
 value=dict(domain)
 if mode=='seconds-string':value['delay_ms']=str(value['delay_ms']//1000)
 return json.dumps(value,separators=(',',':')).encode('utf-8')
def receive(payload,mode):
 if type(payload) is not dict or set(payload)!=set(['fixture_id','delay_ms']) or type(payload['fixture_id']) is not str or payload['fixture_id'] not in ['F1000','F2000']:return None
 n=payload['delay_ms']
 if type(n) is int and n in [1000,2000]:return n
 if mode=='coerce' and type(n) is str:
  try:return int(n)
  except ValueError:return None
 return None
def parse(raw):
 def obj(pairs):
  d={}
  for k,v in pairs:
   if k in d:raise ValueError('duplicate key')
   d[k]=v
  return d
 return json.loads(raw.decode('utf-8'),object_pairs_hook=obj)

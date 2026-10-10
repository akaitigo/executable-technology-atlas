import json,sys
sys.dont_write_bytecode=True
class Refusal(Exception):pass
def require(ok,code):
 if not ok:raise Refusal(code)
def nonfinite(x):raise Refusal('nonfinite_json')
def unique(pairs):
 d={}
 for k,v in pairs:require(k not in d,'duplicate_key');d[k]=v
 return d
def validate(text):
 try:x=json.loads(text,parse_constant=nonfinite,object_pairs_hook=unique)
 except json.JSONDecodeError:raise Refusal('json_syntax')
 require(type(x) is dict and set(x)=={'data','ready','valid'},'shape')
 require(type(x['data']) is int and 0<=x['data']<=255,'data_uint8')
 require(type(x['valid']) is int and x['valid'] in (0,1),'valid_bit')
 require(type(x['ready']) is list and len(x['ready'])<=8,'ready_length')
 require(all(type(v) is int and v in (0,1) for v in x['ready']),'ready_bit');return x
def model(x,mode):
 v=x['valid'];d=x['data'];ticks=[];captured=[]
 for t,r in enumerate(x['ready']):
  pre_v,pre_d=v,d;fire=bool(v and (r or mode=='ignore_ready'));value=d if fire else None
  if fire:captured.append(d)
  # Actual handshake retires the single offer after capture of pre-edge data.
  if v and r:v=0
  elif v and mode=='advance_on_stall':d=(d+1)%256
  ticks.append({'tick':t,'valid':pre_v,'ready':r,'data':pre_d,'capture':fire,'captured':value,'after_valid':v,'after_data':d})
 return {'ticks':ticks,'captured':captured}
def main():
 try:
  text=sys.stdin.read(8193);require(len(text.encode('utf8'))<=4096,'input_size');x=validate(text);result={'status':'observed','input':x,**{m:model(x,m) for m in ['normal','advance_on_stall','ignore_ready']}};code=0
 except Refusal as e:result={'status':'input_refusal','code':str(e),'normal':None,'advance_on_stall':None,'ignore_ready':None};code=2
 print(json.dumps(result,separators=(',',':')));return code
if __name__=='__main__':sys.exit(main())

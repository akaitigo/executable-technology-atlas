import ipaddress,json,math,sys
sys.dont_write_bytecode=True
class Refusal(Exception):pass
def require(ok,code):
 if not ok:raise Refusal(code)
def nonfinite(value):raise Refusal('nonfinite_json')
def finite_float(value):
 x=float(value);require(math.isfinite(x),'nonfinite_json');return x
def unique(pairs):
 d={}
 for k,v in pairs:
  require(k not in d,'duplicate_key');d[k]=v
 return d
def validate(text):
 try:x=json.loads(text,parse_constant=nonfinite,parse_float=finite_float,object_pairs_hook=unique)
 except json.JSONDecodeError:raise Refusal('json_syntax')
 require(type(x) is dict and set(x)=={'packet','chains'},'shape')
 p=x['packet'];cs=x['chains']
 require(type(p) is dict and set(p)=={'source','protocol','dport'},'packet_shape')
 require(type(p['source']) is str,'packet_source')
 try:ip=ipaddress.IPv4Address(p['source'])
 except ipaddress.AddressValueError:raise Refusal('packet_source')
 require(str(ip)==p['source'],'packet_source')
 require(type(p['protocol']) is str and p['protocol'] in ('tcp','udp'),'packet_protocol')
 require(type(p['dport']) is int and 0<=p['dport']<=65535,'packet_port')
 require(type(cs) is list and len(cs)==2,'chains_shape')
 for c in cs:
  require(type(c) is dict and set(c)=={'id','hook','priority','enabled','verdict','policy'},'chain_shape')
  require(type(c['priority']) is int,'priority_type')
  require(type(c['enabled']) is bool,'enabled_type')
  require(c['hook']=='input','hook_subset')
  require(type(c['verdict']) is str and c['verdict'] in ('accept','drop') and type(c['policy']) is str and c['policy'] in ('accept','drop'),'unsupported_verdict')
 require(cs[0]['priority']!=cs[1]['priority'],'duplicate_priority')
 require(all(type(c['id']) is str for c in cs) and {c['id'] for c in cs}=={'source','service'},'chain_ids')
 for c in cs:
  source=c['id']=='source'
  require(c['priority']==(0 if source else 10),'priority_subset')
  require(c['verdict']==('accept' if source else 'drop') and c['policy']==('drop' if source else 'accept'),'fixed_rule_subset')
  require(not source or c['enabled'],'source_enabled_subset')
 return p,sorted(cs,key=lambda c:c['priority'])
def evaluate(p,chains,faulty=False):
 trace=[]
 for c in chains:
  if not c['enabled']:trace.append('skip '+c['id']+' disabled');continue
  trace.append('chain '+c['id']+' priority='+str(c['priority']))
  source=c['id']=='source';rule='trusted-source' if source else 'tcp-dport-22'
  match=p['source']=='10.0.0.1' if source else p['protocol']=='tcp' and p['dport']==22
  trace.append('rule '+rule+' match='+str(match).lower()+(' verdict='+c['verdict'] if match else ''))
  verdict=c['verdict'] if match else c['policy']
  if not match:trace.append('policy '+verdict)
  if verdict=='drop':trace.extend(['drop: stop ruleset','final drop']);return {'final':'drop','trace':trace}
  if faulty:trace.extend(['BUG accept: stop ruleset','final accept']);return {'final':'accept','trace':trace}
  trace.append('accept: next base chain')
 trace.append('final accept');return {'final':'accept','trace':trace}
def main():
 text=sys.stdin.read(8193)
 try:
  require(len(text.encode('utf8'))<=4096,'input_size');p,cs=validate(text)
  result={'status':'observed','packet':p,'ordered_chains':[c['id'] for c in cs],'normal':evaluate(p,cs),'faulty':evaluate(p,cs,True)};code=0
 except Refusal as e:result={'status':'input_refusal','code':str(e),'normal':None,'faulty':None,'trace':[]};code=2
 print(json.dumps(result,separators=(',',':')));return code
if __name__=='__main__':sys.exit(main())

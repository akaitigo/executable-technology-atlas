"""Finite proof receiver: never reads fixture leaves or accepts a request trust anchor."""
import datetime,hashlib,json,re,sys
sys.dont_write_bytecode=True
TRUSTED_ROOT='82ea96439566986e84d7e37227191ea4a6755a371969acad2f9d26d17e079f56'
class Refusal(Exception):pass
def reject(code):raise Refusal(code)
def pairs(items):
 d={}
 for k,v in items:
  if k in d:reject('json_syntax')
  d[k]=v
 return d
def parse(text):
 try:x=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda _:reject('json_syntax'))
 except (ValueError,TypeError):reject('json_syntax')
 if not isinstance(x,dict) or set(x)!=set(['leaf_hex','index','proof','sender_root']):reject('shape')
 if not isinstance(x['leaf_hex'],str) or not re.fullmatch(r'(?:[0-9a-f]{2}){0,16}',x['leaf_hex']):reject('leaf')
 if type(x['index']) is not int or not 0<=x['index']<=3:reject('index')
 if not isinstance(x['proof'],list) or len(x['proof'])!=2:reject('proof_depth')
 for level,p in enumerate(x['proof']):
  if not isinstance(p,dict) or set(p)!=set(['side','hash']):reject('proof_shape')
  if p['side']!=('left' if (x['index']>>level)&1 else 'right'):reject('proof_side')
  if not isinstance(p['hash'],str) or not re.fullmatch('[0-9a-f]{64}',p['hash']):reject('hash')
 if not isinstance(x['sender_root'],str) or not re.fullmatch('[0-9a-f]{64}',x['sender_root']):reject('root')
 return x
def verify(x):
 leaf_input=b'\x00'+bytes.fromhex(x['leaf_hex']);current=hashlib.sha256(leaf_input).digest();leaf_hash=current.hex();trace=[]
 for level,p in enumerate(x['proof']):
  sibling=bytes.fromhex(p['hash']);left,right=(sibling,current) if p['side']=='left' else (current,sibling);preimage=b'\x01'+left+right;parent=hashlib.sha256(preimage).digest()
  trace.append({'level':level,'sibling_side':p['side'],'current_hash':current.hex(),'sibling_hash':sibling.hex(),'left_hash':left.hex(),'right_hash':right.hex(),'preimage_hex':preimage.hex(),'parent_hash':parent.hex()});current=parent
 derived=current.hex();trusted=derived==TRUSTED_ROOT;sender=derived==x['sender_root']
 return {'input':x,'leaf_preimage_hex':leaf_input.hex(),'leaf_hash':leaf_hash,'trace':trace,'derived_root':derived,'sender_root':x['sender_root'],'trusted_root':TRUSTED_ROOT,'sender_match':sender,'trusted_match':trusted,'naive_accept_sender_root':sender,'category':'trusted_match' if trusted else 'root_mismatch','proved_index':x['index'] if trusted else None,'value_uniqueness_claimed':False,'trust_anchor_source':'verifier-owned literal; fixture assumption, not request','units':'bytes and SHA256 digests'}
def main():
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  x=parse(sys.stdin.read());out={'status':'calculated','summary':verify(x),'context':{'synthetic_only':True,'trusted_root_assumed_preheld':True,'trust_distribution_authenticated':False,'content_truth_verified':False,'signature_verified':False,'consensus_executed':False,'unique_history_proved':False,'collision_resistance_proved':False,'NIST_protocol_conformance_claimed':False},'started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};code=0
 except Refusal as e:out={'status':'input_refusal','code':str(e),'summary':None};code=2
 except Exception as e:out={'status':'execution_error','error_class':type(e).__name__,'summary':None};code=3
 print(json.dumps(out,ensure_ascii=False));return code
if __name__=='__main__':sys.exit(main())

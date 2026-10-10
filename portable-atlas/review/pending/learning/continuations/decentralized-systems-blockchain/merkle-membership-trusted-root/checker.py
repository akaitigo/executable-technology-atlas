"""Independent full-tree fixture plus explicit depth2 equations; no producer import."""
import copy,hashlib,json,subprocess,sys
sys.dont_write_bytecode=True
from runner import ROOT,digest,run,snapshot
H=json.loads((ROOT/'hand-oracle.json').read_text());PIN=H['trusted_root']
def oracle(x):
 h=hashlib.sha256(bytes.fromhex('00'+x['leaf_hex'])).hexdigest();p0,p1=x['proof'];a,b=(p0['hash'],h) if x['index']%2 else (h,p0['hash']);m=hashlib.sha256(bytes.fromhex('01'+a+b)).hexdigest();c,d=(p1['hash'],m) if x['index']>=2 else (m,p1['hash']);z=hashlib.sha256(bytes.fromhex('01'+c+d)).hexdigest()
 return h,[(a,b,m),(c,d,z)]
def inspect(out,x):
 assert out['status']=='calculated';s=out['summary'];h,levels=oracle(x);z=levels[-1][-1];trusted=z==PIN;sender=z==x['sender_root'];assert s['input']==x and s['leaf_hash']==h and s['leaf_preimage_hex']=='00'+x['leaf_hex'] and s['derived_root']==z and s['trusted_root']==PIN and s['sender_root']==x['sender_root']
 assert s['sender_match']==sender and s['trusted_match']==trusted and s['naive_accept_sender_root']==sender and s['category']==('trusted_match' if trusted else 'root_mismatch') and s['proved_index']==(x['index'] if trusted else None) and s['value_uniqueness_claimed'] is False
 assert s['trust_anchor_source']=='verifier-owned literal; fixture assumption, not request' and len(s['trace'])==2
 for j,(a,b,parent) in enumerate(levels):
  t=s['trace'][j];assert t['level']==j and t['sibling_side']==x['proof'][j]['side'] and t['sibling_hash']==x['proof'][j]['hash'] and t['current_hash']==(h if j==0 else levels[0][-1]) and t['left_hash']==a and t['right_hash']==b and t['preimage_hex']=='01'+a+b and t['parent_hash']==parent
 ctx=out['context'];assert set(ctx)==set(['synthetic_only','trusted_root_assumed_preheld','trust_distribution_authenticated','content_truth_verified','signature_verified','consensus_executed','unique_history_proved','collision_resistance_proved','NIST_protocol_conformance_claimed']) and all(v is (k in ['synthetic_only','trusted_root_assumed_preheld']) for k,v in ctx.items())
def main():
 before=snapshot();assert hashlib.sha256(b'abc').hexdigest()==H['sha256_vectors']['abc'] and hashlib.sha256(b'').hexdigest()==H['sha256_vectors']['empty']
 # System OpenSSL is a second primitive backend, not a full certification.
 vectors=[]
 for data in [b'',b'abc',bytes.fromhex(H['root_preimage_hex'])]:
  p=subprocess.run(['openssl','dgst','-sha256'],input=data,capture_output=True);assert p.returncode==0 and p.stdout.decode().strip().split()[-1]==hashlib.sha256(data).hexdigest();vectors.append(hashlib.sha256(data).hexdigest())
 lv=[hashlib.sha256(bytes.fromhex(v)).hexdigest() for v in H['leaf_preimages_hex']];parents=[hashlib.sha256(bytes.fromhex('01'+lv[j]+lv[j+1])).hexdigest() for j in [0,2]];assert lv==H['leaf_hashes'] and parents==H['parent_hashes'] and hashlib.sha256(bytes.fromhex('01'+''.join(parents))).hexdigest()==PIN
 rows=json.loads((ROOT/'expected-table.json').read_text())['rows'];valid=[]
 for row in rows:
  p=run(row['input_json']);out=p['result'];ex=row['expected'];assert p['stderr']=='' and out['status']==ex['status']
  if p['exit']==0:
   inspect(out,json.loads(row['input_json']));assert all(out['summary'][k]==ex[k] for k in ['category','sender_match','trusted_match']);valid.append(out)
  else:assert p['exit']==2 and out=={'status':'input_refusal','code':ex['code'],'summary':None}
 rejected=[]
 for name in ['sender-as-trust','request-root-anchor','wrong-leaf-domain','hex-as-bytes','left-right-swap','path-order','omit-level','duplicate-level','index-ignored','unique-value','content-truth','signature','consensus','trust-distribution']:
  out=copy.deepcopy(valid[7] if name in ['sender-as-trust','request-root-anchor'] else valid[0]);s=out['summary']
  if name=='sender-as-trust':s['trusted_match']=True;s['category']='trusted_match';s['proved_index']=0
  elif name=='request-root-anchor':s['trusted_root']=s['sender_root']
  elif name=='wrong-leaf-domain':s['leaf_preimage_hex']=s['input']['leaf_hex']
  elif name=='hex-as-bytes':s['leaf_hash']=hashlib.sha256(('00'+s['input']['leaf_hex']).encode()).hexdigest()
  elif name=='left-right-swap':s['trace'][0]['left_hash'],s['trace'][0]['right_hash']=s['trace'][0]['right_hash'],s['trace'][0]['left_hash']
  elif name=='path-order':s['trace'].reverse()
  elif name=='omit-level':s['trace'].pop()
  elif name=='duplicate-level':s['trace'].append(s['trace'][0])
  elif name=='index-ignored':s['proved_index']=2
  elif name=='unique-value':s['value_uniqueness_claimed']=True
  else:out['context'][{'content-truth':'content_truth_verified','signature':'signature_verified','consensus':'consensus_executed','trust-distribution':'trust_distribution_authenticated'}[name]]=True
  try:inspect(out,s['input'])
  except AssertionError:rejected.append(name)
  else:raise AssertionError('surviving '+name)
 assert before==snapshot();print(json.dumps({'fixed':14,'normal_or_mismatch':8,'refused':6,'mutants_rejected':rejected,'openssl_vectors':vectors,'unit_sha_mtime_unchanged':True}))
if __name__=='__main__':main()

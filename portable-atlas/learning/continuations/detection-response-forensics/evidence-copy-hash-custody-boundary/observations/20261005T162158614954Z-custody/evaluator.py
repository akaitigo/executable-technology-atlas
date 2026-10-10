import hashlib,json,re,shutil,sys,tempfile
from pathlib import Path
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
 require(type(x) is dict and set(x)=={'evidenceID','payload','mutate','handoffs'},'input_shape')
 require(type(x['evidenceID']) is str and re.fullmatch(r'E-[0-9]{3}',x['evidenceID']),'evidence_id')
 p=x['payload'];require(type(p) is str and 1<=len(p)<=256 and all(32<=ord(c)<=126 or c in '\n\t\r' for c in p),'payload_ascii')
 require(type(x['mutate']) is bool,'mutate_type');require(type(x['handoffs']) is list and 1<=len(x['handoffs'])<=4,'handoffs_shape')
 for a in x['handoffs']:
  require(type(a) is dict and set(a)=={'evidenceID','from','to','seq','recordedHash'},'handoff_shape')
  require(type(a['seq']) is int and 1<=a['seq']<=99,'seq_type')
  require(type(a['recordedHash']) is str and re.fullmatch('[0-9a-f]{64}',a['recordedHash']),'hash_shape')
  require(all(type(a[k]) is str and 1<=len(a[k])<=32 for k in ['evidenceID','from','to']),'handoff_labels')
 return x
def hashfile(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ledger(x,h):
 errors=[];previous='collector';trace=[]
 for i,a in enumerate(x['handoffs']):
  checks={'evidenceID':a['evidenceID']==x['evidenceID'],'actor':a['from'] in {'collector','custodian','analyst'} and a['to'] in {'collector','custodian','analyst'},'seq':a['seq']==i+1,'from_link':a['from']==previous,'recordedHash':a['recordedHash']==h}
  for k,ok in checks.items():
   if not ok:errors.append('handoff['+str(i)+'].'+k)
  trace.append({'input':a,'checks':checks});previous=a['to']
 if previous!='analyst':errors.append('final_recipient')
 return errors,trace
def observe(x):
 # All paths are fixed children of a newly owned directory. No supplied path is opened.
 with tempfile.TemporaryDirectory(prefix='atlas-custody-') as name:
  folder=Path(name);original=folder/'original.txt';copied=folder/'copy.txt'
  original.write_bytes(x['payload'].encode('ascii'));initial=original.read_bytes();h=hashfile(original)
  shutil.copyfile(original,copied);before=copied.read_bytes();bh=hashfile(copied)
  if x['mutate']:
   b=bytearray(before);b[0]=32 if b[0]==126 else b[0]+1;copied.write_bytes(bytes(b))
  after=copied.read_bytes();ah=hashfile(copied);preserved=original.read_bytes()==initial and hashfile(original)==h
  errors,trace=ledger(x,h);match=h==ah;normal='mismatch' if not match else 'ledger_refusal' if errors else 'integrity-match'
  result={'status':'observed','evidenceID':x['evidenceID'],'original_ascii':initial.decode('ascii'),'copy_before_ascii':before.decode('ascii'),'copy_after_ascii':after.decode('ascii'),'original_sha256':h,'copy_before_sha256':bh,'copy_after_sha256':ah,'original_unchanged':preserved,'changed_bytes':sum(a!=b for a,b in zip(before,after)),'integrity_match':match,'ledger_errors':errors,'ledger_consistent':not errors,'normal':{'pass':match and not errors,'decision':normal,'claim':'synthetic copy and ledger only'},'faulty':{'pass':match,'decision':'provenance-approved' if match else 'mismatch','claim':'由来も承認済' if match else 'hash不一致'},'authenticity_proven':False,'legal_custody_proven':False,'ledger_trace':trace,'file_trace':['write owned original.txt','shutil.copyfile original.txt -> copy.txt','hash original and copy before mutation']+(['change copy.txt first byte only'] if x['mutate'] else [])+['read and hash copy.txt after mutation','re-read original unchanged','evaluate synthetic handoff ledger']}
 result['temporary_cleanup']=not folder.exists();return result
def main():
 try:
  text=sys.stdin.read(8193);require(len(text.encode('utf8'))<=4096,'input_size');x=validate(text);r=observe(x);code=0
 except Refusal as e:r={'status':'input_refusal','code':str(e),'normal':None,'faulty':None,'temporary_cleanup':'not-created'};code=2
 print(json.dumps(r,ensure_ascii=False,separators=(',',':')));return code
if __name__=='__main__':sys.exit(main())

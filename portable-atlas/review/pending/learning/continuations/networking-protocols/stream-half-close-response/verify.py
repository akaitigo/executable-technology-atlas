import sys
sys.dont_write_bytecode=True
import json,argparse,hashlib,copy,itertools
from pathlib import Path
from fixtures import FIXTURES
from framing import classify,reply,validate
from oracle import HAND,decode,validate_observation
from observe import observe,environment
R=Path(__file__).resolve().parent
SOURCE=['CONTRACT.md','fixtures.py','framing.py','oracle.py','observe.py','verify.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def partitions(b):
 if not b:return [[]]
 if len(b)>6:return [[b],list(bytes([v]) for v in b)]+[[b[:i],b[i:]] for i in range(1,len(b))]
 return [[b[a:z] for a,z in zip([0]+[i for i in range(1,len(b)) if mask&(1<<(i-1))],[i for i in range(1,len(b)) if mask&(1<<(i-1))]+[len(b)])] for mask in range(1<<max(0,len(b)-1))]
def synthetic(function=classify,response=reply):
 rows=[]
 for f in FIXTURES:
  b=bytes.fromhex(f['wire'])
  for chunks in partitions(b):
   d=function(chunks);assert d['kind']==HAND[f['id']][0]==decode(f['wire']);assert response(d).hex()==HAND[f['id']][1]
   rows.append(dict(fixture=f['id'],chunks=[v.hex() for v in chunks],decision=d,reply_hex=response(d).hex()))
 return rows
def guards():
 cases=[]
 def add(name,change,mode='normal',width=1):
  f=copy.deepcopy(FIXTURES[0]);change(f);cases.append((name,f,mode,width))
 for name,v in [('wire_bool',True),('wire_upper','AA'),('wire_odd','0'),('wire_bad','zz'),('wire_over18','00'*19)]:add(name,lambda f,v=v:f.update(wire=v))
 add('extra_key',lambda f:f.update(extra=1));add('missing_key',lambda f:f.pop('wire'));add('id_type',lambda f:f.update(id=True))
 for v in (0,2,True,'1',None):add('width_'+str(v),lambda f:None,width=v)
 for v in ('unknown',False,None):add('mode_'+str(v),lambda f:None,mode=v)
 out=[]
 for name,f,m,w in cases:
  try:validate(f,m,w)
  except ValueError as exc:out.append(dict(name=name,rejected=True,error=str(exc)))
  else:raise AssertionError(name)
 return out
def mutants():
 source=(R/'framing.py').read_text();changes=[('short_header',"len(data)<2","len(data)<1"),('allow17',"size>16","size>17"),('accept_partial_body',"if len(data)<2+size:return dict(kind='body_eof',body_hex='')","if len(data)<2+size:return dict(kind='complete',body_hex=data[2:].hex())"),('ignore_trailing',"if len(data)>2+size:","if False:"),('little_endian',"(data[0]<<8)|data[1]","(data[1]<<8)|data[0]"),('zero_reply_prefix',"len(body).to_bytes(2,'big')","(0).to_bytes(2,'big')")]
 out=[]
 for name,old,new in changes:
  assert old in source;ns={};exec(compile(source.replace(old,new),'mutant-'+name,'exec'),ns);kills=[]
  for f in FIXTURES:
   try:
    for chunks in partitions(bytes.fromhex(f['wire'])):
     d=ns['classify'](chunks);assert d['kind']==HAND[f['id']][0] and ns['reply'](d).hex()==HAND[f['id']][1]
   except (AssertionError,IndexError,ValueError):kills.append(f['id'])
  assert kills;out.append(dict(name=name,killed_by=kills))
 return out
def validate_raw(raw):
 assert len(raw['rows'])==36
 expected_keys={(f['id'],m,w) for f in FIXTURES for m in ('normal','fault') for w in (1,64)}
 assert {(r['fixture'],r['mode'],r['width']) for r in raw['rows']}==expected_keys
 for row in raw['rows']:validate_observation(row,next(f for f in FIXTURES if f['id']==row['fixture']))
 assert len(raw['probes'])==2
 for row,status,kind in zip(raw['probes'],['timeout','execution_failure'],['timeout','closed_recv']):
  assert row['probe']==kind and row['execution_status']==status and row['protocol_outcome']=='undetermined'
  assert row['closed_filenos']==[-1,-1] and row['owned_count']==2 and len(row['errors'])==1
  assert not any(s['result']=='eof' for s in row['trace'])
 assert raw['probes'][0]['errors'][0]['type'] in ('timeout','TimeoutError')
 assert raw['probes'][1]['errors'][0]['type']=='OSError' and raw['probes'][1]['errors'][0]['errno']==9
 return True
def actual():
 data=dict(environment=environment(),rows=[observe(f,m,w) for f in FIXTURES for m in ('normal','fault') for w in (1,64)],probes=[observe(FIXTURES[0],'normal',1,probe=v) for v in ('timeout','closed_recv')])
 return data
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--record');ap.add_argument('--fresh',action='store_true');ap.add_argument('--seal-record',action='store_true');a=ap.parse_args()
 checks=dict(synthetic=synthetic(),guards=guards(),mutants=mutants())
 if a.record:
  p=R/'observations'/a.record;p.mkdir(exist_ok=False);data=actual();data.update(checks);data['source_hashes']={n:sha(R/n) for n in SOURCE}
  (p/'raw.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');validate_raw(data)
 elif a.seal_record:
  hashes={str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}
  (R/'observations/receipt.json').write_text(json.dumps(dict(hashes=hashes,ui_pending=False),indent=2)+'\n')
 else:
  data=json.loads((R/'observations/attempt-01/raw.json').read_text());validate_raw(data)
  for n,h in data['source_hashes'].items():assert sha(R/n)==h
  for n,v in checks.items():assert data[n]==v
  if a.fresh:validate_raw(actual())
 print(json.dumps(dict(status='passed',observations=36,probes=2,synthetic_partitions=len(checks['synthetic']),guards=len(checks['guards']),mutants=len(checks['mutants']),fresh=a.fresh,scope='finite AF_UNIX unit only')))

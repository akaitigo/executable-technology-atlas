# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,tempfile,datetime,platform,hashlib
from pathlib import Path
BASE=dict(templateVersion=1,owner='team-a',description='base')
def desc(v=1,o='team-a',d='base'):return dict(templateVersion=v,owner=o,description=d)
FIXTURES={
'preserve':(BASE,desc(1,'team-b','user'),desc(2)),
 'template-only':(BASE,BASE,desc(2,d='new')),
 'conflict':(BASE,desc(d='user'),desc(2,d='new')),
 'same-change':(BASE,desc(d='new'),desc(2,d='new')),
 'overwrite-fault':(BASE,desc(1,'team-b','user'),desc(2)),
 'owner-conflict':(desc(o='team-c'),desc(o='team-b'),desc(2)),
 'version-conflict':(BASE,desc(2),desc(3)),
 'refusal':(BASE,dict(BASE,unknown='bad'),desc(2)),
 'failure':(BASE,desc(1,'team-b','user'),desc(2))}
def valid(d):return type(d) is dict and set(d)=={'templateVersion','owner','description'} and type(d['templateVersion']) is int and d['templateVersion'] in (1,2,3) and d['owner'] in ('team-a','team-b','team-c') and type(d['description']) is str and d['description'] in ('base','user','new')
def encode(d):return (json.dumps(d,sort_keys=True,separators=(',',':'))+'\n').encode()
_DEFAULT=object()
def run(case,local=_DEFAULT,path='project.json',copies=None):
 r=dict(case=case,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),inputs=None,status='REFUSED_INPUT',setup_writes=0,apply_writes=0,apply_attempts=0,conflicts=[],before_bytes=None,after_bytes=None,final=None,fixture_created=False)
 if case not in FIXTURES:r['error']='unknown case'
 else:
  base,default,new=FIXTURES[case];loc=default if local is _DEFAULT else local;r['inputs']=dict(base=base,local=loc,new=new,path=path)
  if type(path) is not str or path!='project.json' or not all(valid(d) for d in (base,loc,new)):r['error']='fixed flat descriptor and project.json only'
  else:
   with tempfile.TemporaryDirectory(prefix='atlas-threeway-owned-') as tmp:
    root=Path(tmp);target=root/'project.json';target.write_bytes(encode(loc));r.update(setup_writes=1,fixture_created=True,before_bytes=target.read_bytes().decode())
    merged={}
    for k in sorted(base):
     if loc[k]==base[k]:merged[k]=new[k]
     elif new[k]==base[k] or loc[k]==new[k]:merged[k]=loc[k]
     else:r['conflicts'].append(k)
    if case=='overwrite-fault':merged=dict(new);r['conflicts']=[]
    if r['conflicts']:r['status']='CONFLICT'
    else:
     r['apply_attempts']=1
     try:
      if case=='failure':(target/'child').write_bytes(b'fault')
      else:target.write_bytes(encode(merged));r['apply_writes']=1
      r['status']='APPLIED'
     except OSError as e:r.update(status='EXECUTION_FAILURE',error_class=type(e).__name__,errno=e.errno,error_message=str(e).replace(str(root),'<owned-tmp>'))
    r['after_bytes']=target.read_bytes().decode();r['final']=json.loads(r['after_bytes']);r['before_sha256']=hashlib.sha256(r['before_bytes'].encode()).hexdigest();r['after_sha256']=hashlib.sha256(r['after_bytes'].encode()).hexdigest()
    if copies:
     (copies/'before.json').write_bytes(r['before_bytes'].encode());(copies/'after.json').write_bytes(target.read_bytes())
   r['tmp_cleanup']=True
 r['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();return r

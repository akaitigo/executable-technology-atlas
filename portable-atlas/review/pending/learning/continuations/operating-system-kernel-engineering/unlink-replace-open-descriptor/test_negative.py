import json,sys,copy,subprocess
from pathlib import Path
from oracle import check
from syscall_audit import audit
P=Path(__file__).resolve().parent;BASE=json.loads((P/'fixture.json').read_text())[0]['input']
def produce(x):
 r=subprocess.run([sys.executable,'-B','model.py'],input=json.dumps(x),text=True,capture_output=True,cwd=P);return json.loads(r.stdout)
def collect():
 original=produce(BASE);closed=produce(dict(BASE,mode='closed-fd'));mutants=[]
 def mutate(label,fn,source=None,x=None):
  r=copy.deepcopy(source or original);fn(r);detected=False
  try:check(r,x or BASE);audit(r,x or BASE)
  except (AssertionError,KeyError,IndexError,TypeError):detected=True
  mutants.append(dict(id=label,detected=detected))
 mutate('arbitrary-fd-numbers',lambda r:r['runs'][0].__setitem__('fd_numbers',{'old':101,'new':102}))
 mutate('old-fd-reads-new',lambda r:r['runs'][1]['trace'][-1]['old_fd'].__setitem__('bytes','NEW\n'))
 mutate('unlink-path-opened',lambda r:r['runs'][0]['trace'][-1]['pathname'].__setitem__('status','OPENED'))
 mutate('rename-old-fd-rebound',lambda r:r['runs'][1]['trace'][-1]['old_fd'].__setitem__('identity',r['runs'][1]['identities']['new']))
 mutate('same-inode',lambda r:r['runs'][1]['identities'].__setitem__('new',r['runs'][1]['identities']['old']))
 mutate('nlink-still-one',lambda r:r['runs'][0]['trace'][-1]['old_fd'].__setitem__('nlink',1))
 mutate('gap-not-called',lambda r:r['runs'][2].__setitem__('gap_callback_count',0))
 mutate('gap-path-not-missing',lambda r:r['runs'][2]['trace'][1]['pathname'].__setitem__('open_errno',None))
 mutate('fsync-rounded-success',lambda r:r['runs'][0]['fsync_calls'][0].__setitem__('status','RETURNED'))
 mutate('durability-rounded-success',lambda r:r.__setitem__('durability','DURABLE'))
 mutate('cleanup-temp-retained',lambda r:r['runs'][0]['cleanup'].__setitem__('tempdir_removed',False))
 mutate('cleanup-fd-retained',lambda r:r['runs'][0]['cleanup']['fd_closed'].__setitem__('old',False))
 mutate('wrong-syscall-read-bytes',lambda r:next(c for c in r['runs'][0]['syscalls'] if c['operation']=='read').__setitem__('result','X'))
 mutate('wrong-syscall-target',lambda r:r['runs'][0]['syscalls'][0].__setitem__('target','prepared'))
 mutate('wrong-syscall-fd-arg',lambda r:next(c for c in r['runs'][0]['syscalls'] if c['operation']=='read').__setitem__('args',[101,64]))
 mutate('wrong-syscall-open-result',lambda r:r['runs'][0]['syscalls'][0].__setitem__('result',101))
 mutate('wrong-syscall-fstat-inode',lambda r:next(c for c in r['runs'][0]['syscalls'] if c['operation']=='fstat')['result'].__setitem__('identity',[0,1]))
 mutate('wrong-syscall-stat-size',lambda r:next(c for c in r['runs'][0]['syscalls'] if c['operation']=='stat')['result'].__setitem__('size',0))
 mutate('wrong-syscall-write-data',lambda r:next(c for c in r['runs'][0]['syscalls'] if c['operation']=='write')['args'].__setitem__(1,'BAD\n'))
 mutate('wrong-syscall-seek',lambda r:next(c for c in r['runs'][0]['syscalls'] if c['operation']=='lseek').__setitem__('result',1))
 mutate('wrong-span-binding',lambda r:r['runs'][0]['trace'][0].__setitem__('syscall_span',[0,2]))
 mutate('missing-probe-close',lambda r:next(c for c in r['runs'][0]['syscalls'] if c['operation']=='close' and c['target']=='probe_fd').__setitem__('operation','fsync'))
 mutate('missing-cleanup-close',lambda r:next(c for c in r['runs'][0]['syscalls'] if c['operation']=='close' and c['target']=='old_fd').__setitem__('operation','fsync'))
 mutate('closed-read-errno-wrong',lambda r:next(c for c in r['runs'][0]['syscalls'] if c['target']=='old_fd_closed').__setitem__('errno',2),closed,dict(BASE,mode='closed-fd'))
 mutate('closed-read-target-wrong',lambda r:next(c for c in r['runs'][0]['syscalls'] if c['target']=='old_fd_closed').__setitem__('target','new_fd'),closed,dict(BASE,mode='closed-fd'))
 def inserted_allocation(r):
  calls=r['runs'][0]['syscalls'];i=next(c['seq'] for c in calls if c['target']=='old_fd_closed');calls.insert(i,dict(seq=i,operation='open',target='live',args=['live',0],status='RETURNED',result=r['runs'][0]['fd_numbers']['old'],errno=None))
  for n,c in enumerate(calls):c['seq']=n
 mutate('allocation-between-close-and-read',inserted_allocation,closed,dict(BASE,mode='closed-fd'))
 bad=[]
 def invalid(label,fn):
  x=copy.deepcopy(BASE);fn(x);bad.append((label,json.dumps(x)))
 invalid('old-513',lambda x:x.__setitem__('old_payload','x'*513));invalid('new-513',lambda x:x.__setitem__('new_payload','x'*513));invalid('old-unicode',lambda x:x.__setitem__('old_payload','あ'));invalid('new-unicode',lambda x:x.__setitem__('new_payload','é'));invalid('payload-bool',lambda x:x.__setitem__('old_payload',True));invalid('payload-list',lambda x:x.__setitem__('new_payload',[]));invalid('fsync-int',lambda x:x.__setitem__('fsync',1));invalid('fsync-string',lambda x:x.__setitem__('fsync','true'));invalid('unknown-mode',lambda x:x.__setitem__('mode','real-path'));invalid('path-field',lambda x:x.__setitem__('path','user-file'));invalid('missing-field',lambda x:x.pop('mode'));bad.append(('nonobject','[]'));bad.append(('malformed-json','{'))
 refused=[]
 for label,text in bad:
  r=subprocess.run([sys.executable,'-B','model.py'],input=text,text=True,capture_output=True,cwd=P);out=json.loads(r.stdout);refused.append(dict(id=label,exit=r.returncode,result=out,detected=r.returncode==2 and out['status']=='INPUT_REFUSED' and out['mutation_started'] is False))
 return dict(status='passed' if all(m['detected'] for m in mutants+refused) else 'failed',mutants=mutants,refusals=refused)
if __name__=='__main__':
 r=collect()
 if sys.argv[1:]==['--record']:(P/'evidence/negative.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r));sys.exit(r['status']!='passed')

import os,sys,json,tempfile,platform,errno

def validate(x):
 if type(x)!=dict or set(x)!={'old_payload','new_payload','fsync','mode'}:raise ValueError('FIELDS')
 for key in ['old_payload','new_payload']:
  v=x[key]
  if type(v)!=str or len(v)>512 or any(ord(c)>127 for c in v):raise ValueError('ASCII_0_512')
 if type(x['fsync'])!=bool:raise ValueError('FSYNC_BOOL')
 if type(x['mode'])!=str or x['mode'] not in ['compare','missing-source','closed-fd']:raise ValueError('MODE')
 return x

def experiment(x,label):
 trace=[];logs=[];fds={};ids={};closed={};close_errno={};exception=None;gap_count=0;sync=[];root=None;temp=None
 def value(v):
  if isinstance(v,os.stat_result):return dict(identity=[v.st_dev,v.st_ino],size=v.st_size,nlink=v.st_nlink)
  if isinstance(v,bytes):return v.decode('ascii')
  return v
 def call(operation,target,fn,*args):
  row=dict(seq=len(logs),operation=operation,target=target,args=[(a.decode('ascii') if isinstance(a,bytes) else (os.path.basename(a) if isinstance(a,str) else a)) for a in args])
  try:
   result=fn(*args);row.update(status='RETURNED',result=value(result),errno=None);logs.append(row);return result
  except OSError as e:row.update(status='OS_EXCEPTION',result=None,errno=e.errno,name=type(e).__name__);logs.append(row);raise
 def read_all(fd,target):
  call('lseek',target,os.lseek,fd,0,os.SEEK_SET);chunks=[];reads=0
  for _ in range(9):
   b=call('read',target,os.read,fd,64);reads+=1;chunks.append(b)
   if not b:break
  else:raise RuntimeError('BOUNDED_READ_LIMIT')
  eof=call('read',target,os.read,fd,1);offset=call('lseek',target,os.lseek,fd,0,os.SEEK_CUR);return b''.join(chunks).decode('ascii'),reads,eof.decode('ascii'),offset
 def observe_fd(name):
  if closed.get(name):return dict(state='CLOSED')
  fd=fds[name];data,reads,eof,offset=read_all(fd,name+'_fd');s=call('fstat',name+'_fd',os.fstat,fd)
  return dict(state='OPEN',bytes=data,size=s.st_size,nlink=s.st_nlink,identity=[s.st_dev,s.st_ino],seek_result=0,offset_after=offset,eof=eof,read_calls=reads)
 def path_probe():
  try:st=call('stat','live',os.stat,root+'/live')
  except FileNotFoundError:
   try:
    fd=call('open','live',os.open,root+'/live',os.O_RDONLY)
   except FileNotFoundError:return dict(status='ENOENT',bytes=None,identity=None,stat_identity=None,nlink=None,closed_after_probe=None,stat_errno=2,open_errno=2)
   else:call('close','probe_fd',os.close,fd);raise RuntimeError('PATH_CHANGED_DURING_PROBE')
  fd=call('open','live',os.open,root+'/live',os.O_RDONLY)
  try:
   data,_,_,_=read_all(fd,'probe_fd');s=call('fstat','probe_fd',os.fstat,fd)
   return dict(status='OPENED',bytes=data,identity=[s.st_dev,s.st_ino],stat_identity=[st.st_dev,st.st_ino],nlink=s.st_nlink,closed_after_probe=True,stat_errno=None,open_errno=None)
  finally:call('close','probe_fd',os.close,fd)
 def snapshot(phase):
  start=len(logs);old=observe_fd('old');new=observe_fd('new');path=path_probe()
  try:s=call('stat','prepared',os.stat,root+'/prepared');prepared=dict(status='PRESENT',identity=[s.st_dev,s.st_ino],errno=None)
  except FileNotFoundError:prepared=dict(status='ENOENT',identity=None,errno=2)
  trace.append(dict(phase=phase,old_fd=old,new_fd=new,pathname=path,prepared_path=prepared,syscall_span=[start,len(logs)]))
 def close_owned(name):
  if not closed.get(name):call('close',name+'_fd',os.close,fds[name]);closed[name]=True
  try:call('fstat',name+'_fd_after_close',os.fstat,fds[name])
  except OSError as e:close_errno[name]=e.errno
  else:close_errno[name]=None
 status='OBSERVED'
 try:
  temp=tempfile.TemporaryDirectory(prefix='atlas-owned-fd-');root=temp.name
  for name,filename,key in [('old','live','old_payload'),('new','prepared','new_payload')]:
   fd=call('open',filename,os.open,root+'/'+filename,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);fds[name]=fd;closed[name]=False;data=x[key].encode('ascii');pos=0
   # Each payload is bounded; handle partial write without unlimited looping.
   for _ in range(513):
    if pos==len(data):break
    n=call('write',name+'_fd',os.write,fd,data[pos:])
    if n<=0:raise RuntimeError('NO_WRITE_PROGRESS')
    pos+=n
   if not data:call('write',name+'_fd',os.write,fd,b'')
   if pos!=len(data):raise RuntimeError('BOUNDED_WRITE_LIMIT')
   s=call('fstat',name+'_fd',os.fstat,fd);ids[name]=[s.st_dev,s.st_ino]
   if x['fsync']:call('fsync',name+'_fd',os.fsync,fd)
   sync.append(dict(target=name+'_fd',status='RETURNED' if x['fsync'] else 'SKIPPED'))
  snapshot('prepared')
  if label=='producer-failure':raise RuntimeError('INJECTED_PRODUCER_FAILURE')
  if label in ['unlink','gap']:
   call('unlink','live',os.unlink,root+'/live')
   if label=='gap':
    # Deterministic bounded reader callback between two real operations.
    gap_count+=1;snapshot('gap_after_unlink')
   else:snapshot('after_unlink')
  if label in ['replace','gap']:
   call('replace','prepared->live',os.replace,root+'/prepared',root+'/live');snapshot('after_replace')
  if label=='missing-source':
   try:call('replace','missing->live',os.replace,root+'/missing',root+'/live')
   except OSError as e:exception=dict(operation='replace',errno=e.errno,name=type(e).__name__);status='OS_EXCEPTION_OBSERVED'
   else:raise RuntimeError('EXPECTED_OS_EXCEPTION_ABSENT')
   snapshot('after_exception')
  if label=='closed-fd':
   close_owned('old')
   try:call('read','old_fd_closed',os.read,fds['old'],1)
   except OSError as e:exception=dict(operation='read',errno=e.errno,name=type(e).__name__);status='OS_EXCEPTION_OBSERVED'
   else:raise RuntimeError('EXPECTED_OS_EXCEPTION_ABSENT')
   snapshot('after_exception')
 except OSError as e:status='OS_EXCEPTION_UNEXPECTED';exception=dict(operation=logs[-1]['operation'] if logs else 'setup',errno=e.errno,name=type(e).__name__)
 except Exception as e:status='EXECUTION_FAILED';exception=dict(operation='producer',errno=None,name=type(e).__name__)
 finally:
  for name in fds:close_owned(name)
  if temp:temp.cleanup()
 removed=root is not None and not os.path.exists(root)
 kind='CONTROL_GAP' if label=='gap' else ('OS_EXCEPTION' if label in ['missing-source','closed-fd'] else ('PRODUCER_FAILURE' if label=='producer-failure' else 'NORMAL'))
 return status,dict(label=label,kind=kind,trace=trace,identities=ids,fd_numbers=fds,syscalls=logs,fsync_calls=sync,gap_callback_count=gap_count,exception=exception,cleanup=dict(fd_closed=closed,fd_fstat_errno=close_errno,tempdir_removed=removed))

def run(x,fail=False):
 validate(x);labels=['producer-failure'] if fail else (['unlink','replace','gap'] if x['mode']=='compare' else [x['mode']]);runs=[];status='OBSERVED'
 for label in labels:
  s,r=experiment(x,label);runs.append(r)
  if s!='OBSERVED':status=s;break
 return dict(status=status,input_echo=x,mutation_started=True,environment=dict(system=platform.system(),release=platform.release(),python=platform.python_version(),filesystem='UNIDENTIFIED'),runs=runs,durability='UNOBSERVED',cleanup=dict(all_fds_closed=all(all(v is True for v in r['cleanup']['fd_closed'].values()) and all(e==errno.EBADF for e in r['cleanup']['fd_fstat_errno'].values()) for r in runs),tempdirs_removed=all(r['cleanup']['tempdir_removed'] for r in runs)))
if __name__=='__main__':
 try:
  x=validate(json.load(sys.stdin))
  if sys.argv[1:] not in [[],['--fail']]:raise ValueError('ARGUMENT')
 except (ValueError,TypeError) as e:print(json.dumps(dict(status='INPUT_REFUSED',reason=str(e),mutation_started=False)));sys.exit(2)
 r=run(x,sys.argv[1:]==['--fail']);print(json.dumps(r));sys.exit({'OBSERVED':0,'INPUT_REFUSED':2,'EXECUTION_FAILED':3,'OS_EXCEPTION_OBSERVED':4,'OS_EXCEPTION_UNEXPECTED':5}[r['status']])

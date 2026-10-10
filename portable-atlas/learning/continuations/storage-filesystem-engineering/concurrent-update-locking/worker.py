"""Owned child: commands are controller-fixed, never supplied by browser input."""
import sys,json,os,fcntl,datetime
from pathlib import Path
root=Path(sys.argv[1]);name=sys.argv[2];lock=None;value=None;candidate=root/(name+'.new')
def emit(event,**data):
 print(json.dumps(dict(event=event,writer=name,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**data)),flush=True)
emit('ready')
try:
 for line in sys.stdin:
  op=json.loads(line)['op']
  if op=='lock':
   if lock is None:lock=open(root/'update.lock','a+b')
   try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);emit('acquired',lock_inode=os.fstat(lock.fileno()).st_ino)
   except BlockingIOError:emit('would_block',lock_inode=os.fstat(lock.fileno()).st_ino)
  elif op=='read':
   data=(root/'config').read_bytes();value=int(data);emit('read',bytes=data.decode(),value=value,target_inode=(root/'config').stat().st_ino)
  elif op=='write':
   data=(str(value+1)+'\n').encode();candidate.write_bytes(data);emit('write',candidate=candidate.name,bytes=data.decode(),value=value+1)
  elif op=='replace':
   os.replace(candidate,root/'config');emit('rename',finalbytes=(root/'config').read_text(),target_inode=(root/'config').stat().st_ino)
  elif op=='abort':
   candidate.unlink();emit('abort_before_replace')
  elif op=='unlock':fcntl.flock(lock,fcntl.LOCK_UN);emit('released')
  elif op=='close':emit('closing');break
  else:raise ValueError('unsupported controller command')
finally:
 if lock is not None:lock.close()

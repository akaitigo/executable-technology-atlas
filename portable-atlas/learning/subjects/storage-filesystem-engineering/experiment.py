"""Actual task-owned file replacement. Application write-new/replace, not block CoW."""
import hashlib,json,os,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODES=('atomic-commit','atomic-abort','truncate-fail')
class InjectedFailure(Exception):pass

def validate(spec):
 if type(spec) is not dict or set(spec)!={'mode','old','new','cut'}:raise ValueError('mode/old/new/cutだけを持つobjectが必要（外部path不可）')
 if spec['mode'] not in MODES:raise ValueError('未対応mode')
 for k in ('old','new'):
  if type(spec[k]) is not str or not spec[k].isascii() or len(spec[k])>1024:raise ValueError(k+'は0..1024文字ASCII')
 if type(spec['cut']) is not int or not 0<=spec['cut']<=len(spec['new']):raise ValueError('cutはinteger 0..len(new)（bool/float不可）')
 if spec['mode']=='atomic-commit' and spec['cut']!=len(spec['new']):raise ValueError('commitはcut=len(new)のみ')
 return spec

def summary(data):return {'length':len(data),'sha256':hashlib.sha256(data).hexdigest(),'hex':data.hex()}
def execute(spec):
 validate(spec)
 events=[];held=None;td=None;injected=False;unexpected=None;committed=False;temp_name=None
 def event(name,**fields):events.append(dict(seq=len(events),event=name,wall_ns=time.time_ns(),mono_ns=time.monotonic_ns(),**fields))
 def fsync_file(file,role):
  file.flush();event('flush_returned',role=role)
  event('fsync_called',role=role,fd=file.fileno())
  try:os.fsync(file.fileno());event('fsync_returned',role=role)
  except OSError as e:event('fsync_failed',role=role,errno=e.errno);raise
 def snapshot(name,target,candidate):
  path_data=target.read_bytes();held.seek(0);held_data=held.read()
  ps=os.stat(target);hs=os.fstat(held.fileno())
  cs=os.stat(candidate) if candidate.exists() else None
  event(name,path=summary(path_data),held_reader=summary(held_data),candidate=summary(candidate.read_bytes()) if cs else None,path_inode=ps.st_ino,held_inode=hs.st_ino,path_device=ps.st_dev,held_device=hs.st_dev,candidate_inode=cs.st_ino if cs else None,candidate_device=cs.st_dev if cs else None)
 try:
  td=tempfile.TemporaryDirectory(prefix='.owned-',dir=str(ROOT));folder=Path(td.name);temp_name=folder.name
  target=folder/'target.bin';candidate=folder/'new.tmp'
  event('owned_temp_created',relative_directory=temp_name,pid=os.getpid())
  with target.open('xb') as f:f.write(spec['old'].encode('ascii'));fsync_file(f,'initial-old')
  # Unbuffered reader avoids stale Python read-ahead: this observes its open file.
  held=target.open('rb',buffering=0);event('held_reader_opened',fd=held.fileno())
  snapshot('old_ready',target,candidate)
  if spec['mode'].startswith('atomic'):
   with candidate.open('xb') as f:
    event('candidate_created',filename='new.tmp')
    snapshot('candidate_empty',target,candidate)
    prefix=spec['new'][:spec['cut']].encode('ascii');f.write(prefix);fsync_file(f,'candidate')
    snapshot('candidate_written',target,candidate)
   if spec['mode']=='atomic-abort':raise InjectedFailure('after candidate prefix / before replace')
   event('replace_called',src='new.tmp',dst='target.bin')
   os.replace(candidate,target);committed=True;event('replace_returned')
   snapshot('after_replace',target,candidate)
   dfd=os.open(folder,os.O_RDONLY)
   try:
    event('fsync_called',role='directory',fd=dfd)
    try:os.fsync(dfd);event('fsync_returned',role='directory')
    except OSError as e:event('fsync_failed',role='directory',errno=e.errno)
   finally:os.close(dfd);event('directory_fd_closed')
  else:
   with target.open('wb') as f:
    event('truncate_open_returned',filename='target.bin')
    snapshot('after_truncate',target,candidate)
    f.write(spec['new'][:spec['cut']].encode('ascii'));fsync_file(f,'in-place-target')
    snapshot('partial_overwrite',target,candidate)
   raise InjectedFailure('after truncate and prefix overwrite')
 except InjectedFailure as e:
  injected=True;event('injected_exception',type='InjectedFailure',message=str(e))
  snapshot('after_exception',target,candidate)
 except Exception as e:
  unexpected={'type':type(e).__name__,'message':str(e).replace(str(ROOT),'MODULE')}
  event('unexpected_exception',**unexpected)
 finally:
  if held is not None:held.close();event('held_reader_closed')
  if td is not None:
   folder_exists_before=Path(td.name).exists();td.cleanup();event('owned_temp_removed',relative_directory=temp_name,existed_before=folder_exists_before,exists_after=Path(td.name).exists())
 return {'status':'error' if unexpected else 'observed','input':spec,'pid':os.getpid(),'events':events,'committed':committed,'injected_exception':injected,'unexpected':unexpected,'cleanup':{'held_reader_closed':held is None or held.closed,'temp_removed':td is not None and not Path(td.name).exists()},'durability_proven':False,'durability':'power-loss/crash durability not tested; fsync call/return evidence only'}

"""Actual owned Darwin file mmap observation. No oracle imports; no pointer/truncate tricks."""
import mmap,tempfile,datetime,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def exception(e):return dict(type=type(e).__name__,message=str(e),errno=getattr(e,'errno',None))
def execute_mode(mode,fixture,row):
 row.update(mode=mode,length=fixture['length'],offset=fixture['offset'],write_index=fixture['write_index'],write_byte=fixture['write_byte'],pid=os.getpid(),events=[]);events=row['events'];m=observer=f=None;root=None
 try:
  with tempfile.TemporaryDirectory(prefix='.owned-mmap-',dir=ROOT) as d:
   root=Path(d);path=root/'mapped.bin';f=open(path,'w+b');f.write(fixture['initial'].encode('ascii'))
   events.append(dict(event='file_write_buffer',utc=utc(),requested_bytes=fixture['initial']))
   f.flush();events.append(dict(event='file_flush_before_map',utc=utc(),file_bytes=path.read_bytes().decode('ascii')))
   m=mmap.mmap(f.fileno(),fixture['length'],access=getattr(mmap,mode),offset=fixture['offset']);observer=mmap.mmap(f.fileno(),fixture['length'],access=mmap.ACCESS_READ,offset=0)
   def snapshot(event,**extra):events.append(dict(event=event,utc=utc(),mapping_bytes=None if m.closed else m[:].decode('ascii'),observer_bytes=None if observer.closed else observer[:].decode('ascii'),file_bytes=path.read_bytes().decode('ascii'),mapping_closed=m.closed,observer_closed=observer.closed,file_object_closed=f.closed,**extra))
   snapshot('mappings_opened')
   try:m[fixture['write_index']]=fixture['write_byte'];row['write_outcome']='succeeded';snapshot('write_succeeded')
   except TypeError as e:row['write_outcome']='refused';row['exception']=exception(e);snapshot('write_refused',exception=row['exception'])
   try:result=m.flush();snapshot('mapping_flush',flush_outcome='succeeded',flush_return=result)
   except OSError as e:snapshot('mapping_flush',flush_outcome='failed',exception=exception(e))
   m.close();snapshot('mapping_closed')
   observer.close();snapshot('observer_closed')
   f.close();snapshot('file_closed');row['final_file_bytes']=path.read_bytes().decode('ascii')
 finally:
  if m is not None and not m.closed:m.close()
  if observer is not None and not observer.closed:observer.close()
  if f is not None and not f.closed:f.close()
  row['cleanup']=dict(mapping_closed=m is None or m.closed,observer_closed=observer is None or observer.closed,file_closed=f is None or f.closed,temp_removed=root is None or not root.exists())
def execute_boundary(id,fixture,row):
 row.update(id=id,pid=os.getpid(),initial=fixture['initial'],events=[]);root=None;m=None
 try:
  with tempfile.TemporaryDirectory(prefix='.owned-mmap-boundary-',dir=ROOT) as d:
   root=Path(d);path=root/'mapped.bin';path.write_bytes(fixture['initial'].encode('ascii'))
   with open(path,'rb') as f:
    row['offset']=1 if id=='unaligned-offset' else 0;row['length']=5 if id=='overlength' else 1 if id=='unaligned-offset' else 4;row['mappingmode']='ACCESS_READ';row['events'].append(dict(event='attempt',utc=utc(),api='mmap.mmap' if id in ('unaligned-offset','overlength') else 'mapping[index]',index=4 if id=='index-outside' else 0 if id=='closed-read' else None))
    try:
     m=mmap.mmap(f.fileno(),row['length'],access=mmap.ACCESS_READ,offset=row['offset'])
     if id=='closed-read':m.close();row['events'].append(dict(event='close_before_read',utc=utc()))
     if id in ('index-outside','closed-read'):value=m[4 if id=='index-outside' else 0];row['unexpected_value']=value
     row['outcome']='unexpected_acceptance'
    except (OSError,ValueError,IndexError) as e:row['outcome']='refused';row['exception']=exception(e);row['events'].append(dict(event='api_refused',utc=utc(),exception=row['exception']))
    finally:
     if m is not None and not m.closed:m.close()
   row['final_file_bytes']=path.read_bytes().decode('ascii')
 finally:row['cleanup']=dict(mapping_closed=m is None or m.closed,temp_removed=root is None or not root.exists())

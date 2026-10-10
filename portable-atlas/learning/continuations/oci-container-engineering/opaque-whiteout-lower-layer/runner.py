# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import io,tarfile,copy,hashlib,datetime,platform
LOWER=[('d/a','oldA','0'),('d/b','oldB','0'),('keep','k','0')]
CASES=['opaque-before','opaque-after','no-opaque','sequential-fault','escape','absolute','nonempty','symlink','hardlink','duplicate','ordinary-whiteout','directory','failure']
MARKERS={'escape':'../.wh..wh..opq','absolute':'/d/.wh..wh..opq','ordinary-whiteout':'d/.wh.b'}
_DEFAULT=object()
def pack(items):
 out=io.BytesIO()
 with tarfile.open(fileobj=out,mode='w',format=tarfile.USTAR_FORMAT) as t:
  for name,value,kind in items:
   b=value.encode('ascii');info=tarfile.TarInfo(name);info.type=kind.encode();info.size=len(b) if kind=='0' else 0;info.mode=0o644;info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
   if kind in ('1','2'):info.linkname='d/a'
   t.addfile(info,io.BytesIO(b) if kind=='0' else None)
 return out.getvalue()
def read(blob):
 rows=[]
 with tarfile.open(fileobj=io.BytesIO(blob),mode='r:') as t:
  for m in t:
   b=t.extractfile(m).read() if m.isfile() else b''
   rows.append(dict(name=m.name,type=m.type.decode('ascii'),size=m.size,bytes_hex=b.hex(),text=b.decode('ascii'),linkname=m.linkname))
 return rows
class Refusal(Exception):pass
def validate(rows):
 seen=set()
 for m in rows:
  n=m['name'];parts=n.split('/')
  if n.startswith('/') or any(p in ('','.','..') for p in parts) or not n.isascii():raise Refusal('noncanonical-path')
  if n in seen:raise Refusal('duplicate-path')
  seen.add(n)
  if m['type']!='0':raise Refusal('unsupported-entry-type')
  if parts[-1]=='.wh..wh..opq':
   if m['size']!=0:raise Refusal('nonempty-opaque')
   if n!='d/.wh..wh..opq':raise Refusal('unsupported-opaque-location')
  elif any(p.startswith('.wh.') for p in parts):raise Refusal('unsupported-whiteout')
  elif n not in ('d/a','d/b','d/c','keep'):raise Refusal('unsupported-file-path')
def apply(lower,rows,fault=False):
 validate(rows);result=dict(lower)
 if fault:
  for m in rows:
   if m['name']=='d/.wh..wh..opq':result={k:v for k,v in result.items() if not k.startswith('d/')}
   else:result[m['name']]=m['text']
 else:
  if any(m['name']=='d/.wh..wh..opq' for m in rows):result={k:v for k,v in lower.items() if not k.startswith('d/')}
  for m in rows:
   if m['name']!='d/.wh..wh..opq':result[m['name']]=m['text']
 return result

def run(case,payload='newA',marker=_DEFAULT,copies=None):
 marker=MARKERS.get(case,'d/.wh..wh..opq') if marker is _DEFAULT else marker
 r=dict(case=case,inputs=dict(payload=payload,marker=marker),python=platform.python_version(),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='REFUSED_INPUT',lower_members=[],upper_members=[],lower_before=None,lower_after=None,final_map=None,host_extracted=False)
 if case not in CASES or type(payload) is not str or payload not in ('newA','newX') or type(marker) is not str or len(marker)>40 or any(ord(c)<32 or ord(c)>126 for c in marker):r['error']='finite case/payload/marker input required'
 else:
  files=[('d/a',payload,'0'),('d/c','newC','0')];opaque=(marker,'x' if case=='nonempty' else '', '0');items=[opaque]+files if case=='opaque-before' else files+[opaque]
  if case=='no-opaque':items=files
  if case in ('symlink','hardlink'):items=files+[('d/link','','2' if case=='symlink' else '1')]
  if case=='duplicate':items=files+[('d/a','dupe','0')]
  if case=='directory':items=files+[('d/sub','','5')]
  lower_blob=pack(LOWER);upper_blob=b'not a tar' if case=='failure' else pack(items)
  r.update(lower_tar_sha256=hashlib.sha256(lower_blob).hexdigest(),upper_tar_sha256=hashlib.sha256(upper_blob).hexdigest(),lower_tar_size=len(lower_blob),upper_tar_size=len(upper_blob))
  if copies:(copies/'lower.tar').write_bytes(lower_blob);(copies/'upper.tar').write_bytes(upper_blob)
  try:
   lm=read(lower_blob);validate(lm);lower={m['name']:m['text'] for m in lm};before=copy.deepcopy(lower);r.update(lower_members=lm,lower_before=before)
   um=read(upper_blob);r['upper_members']=um;r['final_map']=apply(lower,um,case=='sequential-fault');r['status']='APPLIED'
  except Refusal as e:r.update(status='SUBSET_REFUSED',error=str(e))
  except tarfile.TarError as e:r.update(status='EXECUTION_FAILURE',error_class=type(e).__name__,error_message=str(e))
  r['lower_after']=lower;assert lower==before
 r['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();return r

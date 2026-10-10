# SPDX-License-Identifier: Apache-2.0
import hashlib
# Manual USTAR decoder and literal expectations; no tarfile/runner/applier shared.
LOWER={'d/a':'oldA','d/b':'oldB','keep':'k'}
MAPS={'opaque-before':{'d/a':'newA','d/c':'newC','keep':'k'},'opaque-after':{'d/a':'newA','d/c':'newC','keep':'k'},'no-opaque':{'d/a':'newA','d/b':'oldB','d/c':'newC','keep':'k'},'sequential-fault':{'keep':'k'}}
REJECT={'escape':'noncanonical-path','absolute':'noncanonical-path','nonempty':'nonempty-opaque','symlink':'unsupported-entry-type','hardlink':'unsupported-entry-type','duplicate':'duplicate-path','ordinary-whiteout':'unsupported-whiteout','directory':'unsupported-entry-type'}
MEMBERS={'opaque-before':[('d/.wh..wh..opq','','0'),('d/a','newA','0'),('d/c','newC','0')],'opaque-after':[('d/a','newA','0'),('d/c','newC','0'),('d/.wh..wh..opq','','0')],'no-opaque':[('d/a','newA','0'),('d/c','newC','0')],'sequential-fault':[('d/a','newA','0'),('d/c','newC','0'),('d/.wh..wh..opq','','0')],'escape':[('d/a','newA','0'),('d/c','newC','0'),('../.wh..wh..opq','','0')],'absolute':[('d/a','newA','0'),('d/c','newC','0'),('/d/.wh..wh..opq','','0')],'nonempty':[('d/a','newA','0'),('d/c','newC','0'),('d/.wh..wh..opq','x','0')],'symlink':[('d/a','newA','0'),('d/c','newC','0'),('d/link','','2')],'hardlink':[('d/a','newA','0'),('d/c','newC','0'),('d/link','','1')],'duplicate':[('d/a','newA','0'),('d/c','newC','0'),('d/a','dupe','0')],'ordinary-whiteout':[('d/a','newA','0'),('d/c','newC','0'),('d/.wh.b','','0')],'directory':[('d/a','newA','0'),('d/c','newC','0'),('d/sub','','5')]}
def decode(b):
 rows=[];at=0
 while at+512<=len(b):
  h=b[at:at+512]
  if h==b'\0'*512:assert not any(b[at:]);break
  assert h[257:263]==b'ustar\0' and h[263:265]==b'00'
  checksum=int(h[148:156].rstrip(b'\0 ').strip() or b'0',8);assert checksum==sum(h[:148])+8*32+sum(h[156:])
  assert not h[345:500].rstrip(b'\0')
  size=int(h[124:136].rstrip(b'\0 ').strip() or b'0',8);name=h[:100].split(b'\0',1)[0].decode('ascii');kind=h[156:157].decode('ascii');data=b[at+512:at+512+size]
  if kind=='5' and name.endswith('/'):name=name[:-1]
  assert len(data)==size;rows.append(dict(name=name,type=kind,size=size,bytes_hex=data.hex(),text=data.decode('ascii'),linkname=h[157:257].split(b'\0',1)[0].decode('ascii')));at+=512+((size+511)//512)*512
 return rows

def check(r,files=None):
 c=r['case'];assert r['python']=='3.9.6' and not r['host_extracted'] and r['started_utc']<=r['ended_utc']
 assert r['lower_before']==r['lower_after']==LOWER
 assert [(m['name'],m['text'],m['type']) for m in r['lower_members']]==[('d/a','oldA','0'),('d/b','oldB','0'),('keep','k','0')]
 if c=='failure':assert r['status']=='EXECUTION_FAILURE' and r['error_class']=='ReadError' and r['error_message']=='truncated header' and r['final_map'] is None
 else:
  assert [(m['name'],m['text'],m['type']) for m in r['upper_members']]==MEMBERS[c]
  if c in MAPS:assert r['status']=='APPLIED' and r['final_map']==MAPS[c]
  else:assert r['status']=='SUBSET_REFUSED' and r['error']==REJECT[c] and r['final_map'] is None
 for m in r['lower_members']+r['upper_members']:
  assert m['size']==len(bytes.fromhex(m['bytes_hex'])) and bytes.fromhex(m['bytes_hex']).decode()==m['text']
 if files:
  for layer in ('lower','upper'):
   b=(files/(layer+'.tar')).read_bytes();assert hashlib.sha256(b).hexdigest()==r[layer+'_tar_sha256'] and len(b)==r[layer+'_tar_size']
   if layer=='upper' and c=='failure':assert b==b'not a tar'
   else:assert decode(b)==r[layer+'_members']

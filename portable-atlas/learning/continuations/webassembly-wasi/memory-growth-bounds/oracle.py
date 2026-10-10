# SPDX-License-Identifier: Apache-2.0
import hashlib
# Literal byte contract independent of JS section builder and runtime.
HEX='0061736d0100000001060160017f017f0303020000050401010102071903066d656d6f72790200056c6f61643800000467726f7700010a1002070020002d00000b0600200040000b'
def val(op,value,**extra):return dict(op=op,**extra,outcome='value',kind='undefined' if value is None else 'boolean' if type(value) is bool else 'number',value=value)
def err(op,cls,**extra):return dict(op=op,**extra,outcome='exception',error_class=cls)
def events(name):
 initial=[val('initial-bytes',65536),val('initial-shared',False),val('initial-resizable',False),dict(op='host-writes',writes=[[0,7],[65535,171]])]
 if name=='last-byte':return initial+[val('core-load8',171,address=65535)]
 if name=='initial-oob':return initial+[err('core-load8','RuntimeError',address=65536)]
 if name=='grow-one':return initial+[val('js-grow',1,delta=1),val('new-bytes',131072),val('buffer-replaced',True),val('old-buffer-bytes',0),val('old-typed-length',0),val('old-typed-index',None),err('old-typed-slice','TypeError'),err('old-data-byteLength','TypeError'),err('old-data-get','TypeError'),val('new-typed-length',131072),val('new-data-get',7),val('core-load8',7,address=0),val('core-load8',171,address=65535),val('core-load8',0,address=65536),val('core-load8',0,address=131071),err('core-load8','RuntimeError',address=131072)]
 if name in ('js-max','core-max'):return initial+([err('js-grow','RangeError',delta=2)] if name=='js-max' else [val('core-grow',-1,delta=2)])+[val('after-bytes',65536),val('buffer-same',True),val('old-typed-length',65536),val('old-data-get',7),val('core-load8',171,address=65535)]
 return []
STATUS={'last-byte':'LOAD_OK','initial-oob':'EXPECTED_TRAP','grow-one':'GROWN','js-max':'EXPECTED_JS_GROW_FAILURE','core-max':'EXPECTED_CORE_GROW_FAILURE','host-refusal':'REFUSED_INPUT','execution-failure':'EXECUTION_FAILURE'}
def check_refusal(r):
 assert r['status']=='REFUSED_INPUT' and r['stage']=='host-validation' and not r['instantiated'] and r['events']==[] and r['module_hex'] is None and r['module_sha256'] is None
 assert r['error']=='address number/integer 0..131072 required'
 a=r['address'];assert type(a) not in (int,float) or int(a)!=a or not 0<=a<=131072
 return True
def check(r):
 name=r['case'];assert r['status']==STATUS[name]
 assert r['started_utc'].endswith('Z') and r['ended_utc'].endswith('Z') and r['started_utc']<=r['ended_utc']
 if name=='host-refusal':return check_refusal(r)
 if name=='execution-failure':
  assert not r['instantiated'] and r['events']==[] and r['stage']=='executor' and r['module_hex'] is None and r['module_sha256'] is None
  assert r['error_class']=='Error' and r['error_message']=='injected host executor unavailable';return True
 assert r['instantiated'] and r['stage']=='complete' and r['module_hex']==HEX and r['module_sha256']==hashlib.sha256(bytes.fromhex(HEX)).hexdigest()
 observed=[]
 for e in r['events']:
  if e.get('outcome')=='exception':assert isinstance(e['error_message'],str) and e['error_message']
  observed.append({k:v for k,v in e.items() if k!='error_message'})
 assert observed==events(name),(name,observed)
 return True
def binary_contract():
 b=bytes.fromhex(HEX);assert len(b)==72 and b[:8]==bytes([0,97,115,109,1,0,0,0]);at=8;sections={}
 while at<len(b):
  sid,size=b[at],b[at+1];at+=2;assert sid not in sections;sections[sid]=list(b[at:at+size]);at+=size
 assert at==len(b) and list(sections)==[1,3,5,7,10]
 assert sections[1]==[1,96,1,127,1,127] and sections[3]==[2,0,0] and sections[5]==[1,1,1,2]
 assert sections[7]==[3,6,109,101,109,111,114,121,2,0,5,108,111,97,100,56,0,0,4,103,114,111,119,0,1]
 assert sections[10]==[2,7,0,32,0,45,0,0,11,6,0,32,0,64,0,11]
 return dict(bytes=72,memory_min=1,memory_max=2,shared=False,load_opcode='i32.load8_u',grow_opcode='memory.grow')

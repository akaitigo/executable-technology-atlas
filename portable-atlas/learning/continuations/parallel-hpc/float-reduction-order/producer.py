# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import math,platform,datetime
VALUES=[1e16,1.0,-1e16,1.0]
CASES=['left','tree','fsum','drop-small','drop-cancel','refusal','failure']
_DEFAULT=object()
def run(name,values=_DEFAULT):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=dict(case=name,started_utc=start,python=platform.python_version(),radix=sys.float_info.radix,mantissa=sys.float_info.mant_dig,rounds=sys.float_info.rounds,inputs=VALUES if values is _DEFAULT else values,ids=[],count=0,steps=[],result=None)
 v=r['inputs']
 if name not in CASES or type(v) is not list or len(v)!=4 or any(type(x) not in (int,float) or not math.isfinite(x) for x in v) or v!=VALUES or name=='refusal':r.update(status='REFUSED_INPUT',stage='validation',error='fixed finite vector required')
 else:
  try:
   if name=='failure':raise RuntimeError('injected executor failure')
   ids=[0,2,3] if name=='drop-small' else [1,3] if name=='drop-cancel' else [0,1,2,3];xs=[float(v[i]) for i in ids];r.update(ids=ids,count=len(ids))
   if name=='tree':
    row=xs
    while len(row)>1:
     row=[row[i]+row[i+1] if i+1<len(row) else row[i] for i in range(0,len(row),2)];r['steps'].append(row[:])
    total=row[0]
   elif name=='fsum':total=math.fsum(xs);r['steps']=[total]
   else:
    total=0.0
    for x in xs:total=total+x;r['steps'].append(total)
   r.update(status='INCLUSION_VIOLATION' if ids!=[0,1,2,3] else 'OK',stage='complete',result=total)
  except Exception as e:r.update(status='EXECUTION_FAILURE',stage='executor',error_class=type(e).__name__,error_message=str(e))
 r['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();return r

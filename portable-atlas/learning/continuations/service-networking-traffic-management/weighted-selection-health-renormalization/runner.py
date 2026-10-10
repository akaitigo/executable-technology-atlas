# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import datetime,platform,json
from pathlib import Path
CASES=json.loads((Path(__file__).parent/'hand-oracle.json').read_text())['inputs']
def pick(slot,bounds,fail):
 if fail:raise RuntimeError('injected selector failure')
 for name,start,end in bounds:
  if start<=slot<end:return name
 raise RuntimeError('missing bucket')
def run(a=1,b=3,ha=True,hb=True,slot=None,fault=False,fail=False):
 r=dict(inputs=dict(a=a,b=b,ha=ha,hb=hb,slot=slot,fault=fault,fail=fail),python=platform.python_version(),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='REFUSED',candidates=[],bounds=[],total=None,trace=[])
 if any(type(w) is not int or not 0<=w<=4 for w in (a,b)) or any(type(v) is not bool for v in (ha,hb,fault,fail)):r['reason']='integer weights 0..4 and boolean health required'
 else:
  endpoints=[('A',a,ha),('B',b,hb)];eligible=[(n,w,h) for n,w,h in endpoints if h and w>0]
  if not eligible:r.update(total=0,reason='no healthy positive weight')
  else:
   candidates=[(n,w,h) for n,w,h in endpoints if w>0] if fault else eligible
   total=0
   for n,w,h in candidates:r['candidates'].append(n);r['bounds'].append([n,total,total+w]);total+=w
   r['total']=total
   if slot is not None and (type(slot) is not int or not 0<=slot<total):r['reason']='integer slot in [0,total) required'
   else:
    try:
     for s in range(total) if slot is None else [slot]:
      selected=pick(s,r['bounds'],fail);healthy=ha if selected=='A' else hb
      r['trace'].append(dict(slot=s,selected=selected,healthy=healthy,outcome='SELECTED' if healthy else 'LOSS'))
     r['status']='SELECTED'
    except RuntimeError as e:r.update(status='EXECUTION_FAILURE',error_class=type(e).__name__,error_message=str(e),attempted_slot=s)
 r['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();return r
if __name__=='__main__':
 c=sys.argv[1] if len(sys.argv)>1 else 'normal';print(json.dumps(run(*CASES[c]),ensure_ascii=False,indent=2))

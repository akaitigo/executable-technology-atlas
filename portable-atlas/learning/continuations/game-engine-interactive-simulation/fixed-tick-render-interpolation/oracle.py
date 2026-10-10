"""Independent rational check; never imports JS producer."""
from fractions import Fraction as F
import json
from pathlib import Path
P=Path(__file__).resolve().parent
FIELDS=('previous','current','remainderMs','alpha','render','stateAfterRender','totalTicks')
def expected(inp):
    # batch tick counts from cumulative time, not producer's while-tick loop
    prev=cur=F(0); elapsed=0;old_count=0;rows=[]
    for d in inp['framesMs']:
        elapsed+=d; count,rem=divmod(elapsed,20); n=count-old_count
        if n: prev=cur+20*(n-1);cur=cur+20*n
        a=F(rem,20);render=(1-a)*prev+a*cur
        after=render if inp['mode']=='FAULT_WRITEBACK' else cur
        rows.append([str(prev),str(cur),rem,str(a),str(render),str(after),count])
        cur=after;old_count=count
    return rows
def check(result, inp, literal=None):
    if literal is None:
        assert result['status']=='REFUSED' and result['trace']==[] and result['ticks']==[]
        return
    assert result['status']=='OK' and result['input']==inp
    rows=[[r[k] for k in FIELDS] for r in result['trace']]
    assert rows==literal==expected(inp),(rows,literal)
    elapsed=0;tick=0;state='0'
    for i,(d,r) in enumerate(zip(inp['framesMs'],result['trace'])):
        assert r['frame']==i and r['stateBefore']==state
        elapsed+=d;assert r['deltaMs']==d and r['syntheticMs']==elapsed
        tt=[t for t in result['ticks'] if t['frame']==i]
        prev=F(state)
        for t in tt:
            tick+=1;assert t==dict(frame=i,tick=tick,previous=str(prev),current=str(prev+20),stepMs=20);prev+=20
        assert tick==r['totalTicks'];state=r['stateAfterRender']

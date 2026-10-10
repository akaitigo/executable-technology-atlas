# SPDX-License-Identifier: Apache-2.0
"""Independent prefix service/ownership check using prewritten literal schedules. No model import."""
def check(result,hand):
 h=hand[result['mode']];assert result['cpu']==h['cpu'] and result['finish']==h['finish']
 assert [r['owner'] for r in result['rows']]==h['owner']
 assert [r['tasks']['L']['effective'] for r in result['rows']]==h['effective_L']
 assert result['blocking']==h['blocking'] and result['block_start']==h['block_start'] and result['block_end']==h['block_end']
 specs={'L':(0,3,'K',1,8),'H':(1,1,'K',3,result['h_deadline']),'M':(1,4,None,2,8)}
 for t,row in enumerate(result['rows']):
    assert row['time']==t and row['dispatch']==(h['cpu'][t] if t<8 else None)
    ready=[];blocked=[]
    for id,(a,w,lock,p,due) in specs.items():
        served=sum(1 for v in h['cpu'][:t] if v==id);done=served==w;isblocked=id=='H' and h['blocked_H'][t]
        state='done' if done else 'unreleased' if t<a else 'blocked' if isblocked else 'ready'
        expected=dict(arrival=a,work=w,remaining=w-served,lock=lock,base=p,effective=(h['effective_L'][t] if id=='L' else p),deadline=due,state=state,finish=(h['finish'][id] if done else None),miss=(h['finish'][id]>due and t>=due))
        assert row['tasks'][id]==expected
        if state=='ready':ready.append(id)
        if state=='blocked':blocked.append(id)
    assert row['ready']==sorted(ready) and row['blocked']==blocked
    if row['owner']:assert row['tasks'][row['owner']]['lock']=='K' and row['tasks'][row['owner']]['state']=='ready'
 assert result['work']=={'L':3,'H':1,'M':4} and len(result['cpu'])==8
 assert result['lateness']=={id:h['finish'][id]-s[4] for id,s in specs.items()}
 assert result['misses']==sorted(id for id,s in specs.items() if h['finish'][id]>s[4])
 # Explicit event ownership oracle: acquisition/release pair boundaries, independent of scheduler.
 expected=[(0,'acquire','L'),(h['finish']['L'],'release','L'),(h['finish']['L'],'acquire','H'),(h['finish']['H'],'release','H')]
 assert [(e['time'],e['event'],e['task']) for e in result['events'] if e['event'] in ('acquire','release')]==expected

# SPDX-License-Identifier: Apache-2.0
import copy

def simulate(mode,h_deadline=4):
 if mode not in ('none','pi') or not isinstance(mode,str):raise ValueError('mode must be none or pi')
 if type(h_deadline) is not int or h_deadline not in (2,4):raise ValueError('H deadline must be integer 2 or 4')
 tasks={id:dict(arrival=a,work=w,remaining=w,lock=lock,base=p,effective=p,deadline=(h_deadline if id=='H' else 8),state='unreleased',finish=None,miss=False) for id,a,w,lock,p in [('L',0,3,'K',1),('H',1,1,'K',3),('M',1,4,None,2)]}
 owner=None;rows=[];cpu=[];block_start=None;block_end=None;events=[]
 for t in range(9):
    for id,d in tasks.items():
        if d['arrival']==t:d['state']='ready';events.append(dict(time=t,event='arrival',task=id))
    for id in sorted(tasks,key=lambda id:(-tasks[id]['base'],id)):
        d=tasks[id]
        if d['state'] in ('ready','blocked') and d['lock'] and owner!=id:
            if owner is None:
                owner=id;d['state']='ready';events.append(dict(time=t,event='acquire',task=id))
                if id=='H' and block_start is not None:block_end=t
            elif d['state']!='blocked':
                d['state']='blocked';events.append(dict(time=t,event='block',task=id))
                if id=='H':block_start=t
    for d in tasks.values():d['effective']=d['base']
    if mode=='pi' and owner:
        waiters=[d['base'] for d in tasks.values() if d['state']=='blocked']
        tasks[owner]['effective']=max([tasks[owner]['base']]+waiters)
    for d in tasks.values():
        if d['state']!='done' and d['arrival']<=t and t>=d['deadline']:d['miss']=True
    ready=[id for id,d in tasks.items() if d['state']=='ready'];run=min(ready,key=lambda id:(-tasks[id]['effective'],id)) if ready else None
    rows.append(dict(time=t,dispatch=run if t<8 else None,owner=owner,ready=sorted(ready),blocked=sorted(id for id,d in tasks.items() if d['state']=='blocked'),tasks=copy.deepcopy(tasks)))
    if t==8:break
    if run is None:raise AssertionError('unexpected idle')
    cpu.append(run);d=tasks[run];d['remaining']-=1
    if d['remaining']==0:
        d['finish']=t+1;d['state']='done';events.append(dict(time=t+1,event='finish',task=run))
        if owner==run:owner=None;events.append(dict(time=t+1,event='release',task=run))
 return dict(mode=mode,h_deadline=h_deadline,rows=rows,cpu=cpu,events=events,block_start=block_start,block_end=block_end,blocking=block_end-block_start,finish={id:d['finish'] for id,d in tasks.items()},work={id:d['work'] for id,d in tasks.items()},lateness={id:d['finish']-d['deadline'] for id,d in tasks.items()},misses=sorted(id for id,d in tasks.items() if d['miss']))

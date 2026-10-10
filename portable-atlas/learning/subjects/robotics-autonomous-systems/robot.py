# SPDX-License-Identifier: Apache-2.0
"""Finite point-robot grid toy. No hardware, ROS, sensor processing or dynamics."""
from collections import deque
import copy
VERSION='finite-point-grid-1'
DIRECTIONS=((1,0),(0,-1),(-1,0),(0,1))


def validate(f):
    if not isinstance(f,dict):raise ValueError('fixture must be object')
    w,h=f.get('width'),f.get('height')
    if any(type(v) is not int or not 1<=v<=16 for v in (w,h)):raise ValueError('dimensions must be integer 1..16')
    def cell(p):
        if not isinstance(p,list) or len(p)!=2 or any(type(v) is not int for v in p):raise ValueError('cell needs two integers')
        if not 0<=p[0]<w or not 0<=p[1]<h:raise ValueError('cell outside finite grid')
        return tuple(p)
    start,goal=cell(f.get('start')),cell(f.get('goal'))
    obstacles=f.get('obstacles')
    if not isinstance(obstacles,list):raise ValueError('obstacles must be list')
    blocked={cell(p) for p in obstacles}
    if len(blocked)!=len(obstacles):raise ValueError('duplicate obstacle')
    if start in blocked or goal in blocked:raise ValueError('start/goal must be free')
    budget=f.get('move_budget')
    if type(budget) is not int or not 0<=budget<=64:raise ValueError('move budget must be integer 0..64')
    update=f.get('update')
    if update is not None:
        if not isinstance(update,dict) or set(update)!={'after_moves','cell'}:raise ValueError('fixed update requires after_moves/cell')
        tick=update['after_moves'];p=cell(update['cell'])
        if type(tick) is not int or not 0<=tick<=64:raise ValueError('update tick must be integer 0..64')
        if p in blocked or p==start:raise ValueError('update must add a new non-start obstacle')
    return w,h,start,goal,blocked,budget


def bfs(w,h,start,goal,blocked):
    queue=deque([start]);parent={start:None};expanded=[]
    while queue:
        here=queue.popleft();expanded.append(list(here))
        if here==goal:
            path=[]
            while here is not None:path.append(list(here));here=parent[here]
            return dict(path=path[::-1],expanded=expanded)
        for dx,dy in DIRECTIONS:
            nxt=(here[0]+dx,here[1]+dy)
            if 0<=nxt[0]<w and 0<=nxt[1]<h and nxt not in blocked and nxt not in parent:
                parent[nxt]=here;queue.append(nxt)
    return dict(path=[],expanded=expanded)


def segment_contact(a,b,cell):
    """Slab clipping against a CLOSED unit cell. Touching boundary counts as collision."""
    lo,hi=0.,1.
    for axis in (0,1):
        delta=b[axis]-a[axis];lower,upper=cell[axis]-.5,cell[axis]+.5
        if delta==0:
            if not lower<=a[axis]<=upper:return None
        else:
            enter,leave=(lower-a[axis])/delta,(upper-a[axis])/delta
            if enter>leave:enter,leave=leave,enter
            lo=max(lo,enter);hi=min(hi,leave)
            if lo>hi:return None
    return lo


def collision(a,b,blocked):
    contacts=[]
    for cell in sorted(blocked):
        t=segment_contact(a,b,cell)
        if t is not None:contacts.append(dict(cell=list(cell),t=t,point=[a[i]+t*(b[i]-a[i]) for i in (0,1)]))
    return sorted(contacts,key=lambda c:(c['t'],c['cell']))


def naive(f):
    w,h,start,goal,blocked,budget=validate(f)
    hits=collision(start,goal,blocked)
    return dict(strategy='naive straight line; no planning',status='COLLISION' if hits else 'CLEAR',segment=[list(start),list(goal)],contacts=hits,
                scope='Initial map only; Euclidean segment is not four-neighbor shortest path or executable robot trajectory')


def execute(f,policy='replan'):
    if policy not in ('replan','stop','ignore-update'):raise ValueError('unknown update policy')
    w,h,start,goal,blocked,budget=validate(f)
    known=set(blocked);world=set(blocked);pos=start;moves=0;world_version=0;known_version=0;revealed=False;trace=[];plans=[]
    def emit(event,**details):
        trace.append(dict(index=len(trace),event=event,position=list(pos),moves=moves,known_version=known_version,world_version=world_version,
                          known_obstacles=[list(p) for p in sorted(known)],world_obstacles=[list(p) for p in sorted(world)],details=details))
    def plan():
        result=bfs(w,h,pos,goal,known);plans.append(dict(start=list(pos),map_version=known_version,obstacles=[list(p) for p in sorted(known)],**result))
        return result['path']
    def finish(status,reason,**details):
        emit(status,reason=reason,**details)
        return dict(status=status,reason=reason,policy=policy,moves=moves,move_budget=budget,position=list(pos),trace=trace,plans=plans,
                    scope='Fixed observed update, exact point position, zero-size robot; no real sensor, ROS, dynamics or safety guarantee')
    path=plan();emit('PLAN',path=path,expanded=plans[-1]['expanded'])
    if not path:return finish('NO_PATH','initial map has no four-neighbor route')
    update=f.get('update')
    for _ in range(budget+2):
        if update and not revealed and moves==update['after_moves']:
            new=tuple(update['cell']);world.add(new);world_version+=1;revealed=True
            if policy!='ignore-update':known.add(new);known_version=world_version
            emit('OBSERVATION',new_obstacle=list(new),applied=policy!='ignore-update',fixed_input=True)
            if pos in world:return finish('OCCUPIED_POSITION','observation marks current point occupied; no safe retreat modeled')
        if pos==goal:return finish('REACHED','goal center reached within toy model')
        if moves>=budget:return finish('BUDGET_EXHAUSTED','no further move; observations/replanning do not consume move budget')
        nxt=tuple(path[1]);known_hits=collision(pos,nxt,known)
        emit('CHECK',target=list(nxt),known_contacts=known_hits)
        if known_hits:
            emit('STOP_BEFORE',target=list(nxt),contacts=known_hits)
            if policy=='stop':return finish('STOPPED','next edge blocked in updated known map')
            path=plan();emit('REPLAN',path=path,expanded=plans[-1]['expanded'])
            if not path:return finish('NO_REPLAN','updated map has no route from stopped point')
            nxt=tuple(path[1]);assert not collision(pos,nxt,known)
        world_hits=collision(pos,nxt,world)
        if world_hits:
            # Intentional stale-map counterexample: record simulated contact, do not enter blocked cell.
            return finish('COLLISION','stale-map commanded edge intersects actual fixture obstacle',target=list(nxt),contacts=world_hits)
        previous=list(pos);pos=nxt;moves+=1;path=path[1:];emit('MOVE',from_position=previous,target=list(pos))
    raise AssertionError('finite mission bound exceeded')

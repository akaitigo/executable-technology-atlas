# SPDX-License-Identifier: Apache-2.0
from collections import deque
MODES=['opposite','same-order','retry'];INITIAL=(0,0,-1,-1)
def orders(mode):return [(0,1),(0,1) if mode=='same-order' else (1,0)]
def validate_mode(mode):
    if mode not in MODES:raise ValueError('mode must be opposite/same-order/retry')
def validate_state(s,mode):
    validate_mode(mode)
    if not isinstance(s,(tuple,list)) or len(s)!=4 or any(type(x) is not int for x in s):raise ValueError('four exact integers required')
    if any(pc not in ([0,1,2,3,4] if mode=='retry' else [0,1,2,3]) for pc in s[:2]) or any(o not in [-1,0,1] for o in s[2:]):raise ValueError('pc/owner outside domain')
    for p,(first,second) in enumerate(orders(mode)):
        owned={lock for lock in range(2) if s[2+lock]==p};expected=set() if s[p] in [0,3] else {first} if s[p] in [1,4] else {0,1}
        if owned!=expected:raise ValueError('pc and held-lock ownership disagree')
def successors(state,mode):
    validate_state(state,mode);result=[]
    for p,(first,second) in enumerate(orders(mode)):
        s=list(state);pc=s[p];action=None
        if pc==0 and s[2+first]==-1:s[2+first]=p;s[p]=1;action='acquire-first'
        elif pc==1:
            if s[2+second]==-1:s[2+second]=p;s[p]=2;action='acquire-second'
            elif mode=='retry':s[p]=4;action='observe-failure'
        elif pc==2:
            s[2]=s[3]=-1;s[p]=3;action='complete-release'
        elif pc==4:s[2+first]=-1;s[p]=0;action='release-retry'
        if action:result.append(dict(process=p,action=action,target=tuple(s)))
    return result
def sid(s):return ','.join(map(str,s))
def explore(mode):
    validate_mode(mode);queue=deque([INITIAL]);seen={INITIAL};parent={};edges=[];states=[];dist={INITIAL:0}
    while queue:
        s=queue.popleft();out=successors(s,mode);states.append(dict(id=sid(s),state=list(s),distance=dist[s],enabled=[dict(process=e['process'],action=e['action'],target=sid(e['target'])) for e in out],completed=all(pc==3 for pc in s[:2]),deadlock=not out and not all(pc==3 for pc in s[:2]),safe=not(s[0]==s[1]==2)))
        for e in out:
            target=e['target'];edge=dict(source=sid(s),target=sid(target),process=e['process'],action=e['action']);edges.append(edge)
            if target not in seen:seen.add(target);dist[target]=dist[s]+1;parent[target]=edge;queue.append(target)
    byid={r['id']:r for r in states};adj={r['id']:[] for r in states}
    for edge in edges:adj[edge['source']].append(edge)
    def path_to(target):
        path=[]
        while target!=INITIAL:
            e=parent[target];path.append(e);target=tuple(map(int,e['source'].split(',')))
        return list(reversed(path))
    deadlocks=[s for s in states if s['deadlock']];terminal=[s for s in states if s['completed']]
    deadtrace=path_to(tuple(min(deadlocks,key=lambda s:s['distance'])['state'])) if deadlocks else None
    completion=path_to(tuple(terminal[0]['state'])) if terminal else None
    cycles=[]
    for anchor in sorted(adj):
        if byid[anchor]['completed']:continue
        frontier=deque([(anchor,[])]);visited={anchor}
        found=None
        while frontier and found is None:
            node,path=frontier.popleft()
            for edge in adj[node]:
                if byid[edge['target']]['completed']:continue
                candidate=path+[edge]
                if edge['target']==anchor:found=candidate;break
                if edge['target'] not in visited:visited.add(edge['target']);frontier.append((edge['target'],candidate))
        if found:cycles.append(found)
    cycle=min(cycles,key=lambda p:(len(p),p[0]['source'])) if cycles else None
    prefix=path_to(tuple(map(int,cycle[0]['source'].split(',')))) if cycle else None
    return dict(mode=mode,initial=sid(INITIAL),states=states,edges=edges,deadlock_count=len(deadlocks),terminal_count=len(terminal),safety_violations=sum(not s['safe'] for s in states),shortest_deadlock_trace=deadtrace,completion_trace=completion,noncompletion_cycle=cycle,cycle_prefix=prefix,fairness='none; cycle existence is not inevitable starvation under fairness')

"""Finite directed graph searches, stdlib; no oracle import."""
import collections,heapq,itertools

def validate(f):
    nodes=f['nodes'];edges=f['edges'];h=f['h']
    if not 1<=len(nodes)<=5 or len(set(nodes))!=len(nodes):return 'NODE_BOUND'
    if f['start'] not in nodes or f['goal'] not in nodes:return 'UNKNOWN_NODE'
    if len({(u,v) for u,v,c in edges})!=len(edges):return 'DUPLICATE_EDGE'
    if any(u not in nodes or v not in nodes or type(c) is not int for u,v,c in edges):return 'INVALID_EDGE'
    if any(c<0 for u,v,c in edges):return 'NEGATIVE_COST'
    if set(h)!=set(nodes) or any(type(v) is not int or v<0 for v in h.values()) or h[f['goal']]!=0:return 'INVALID_HEURISTIC'
    if any(h[u]>c+h[v] for u,v,c in edges):return 'INCONSISTENT_HEURISTIC'
    return None

def bfs(f):
    queue=collections.deque([(f['start'],[f['start']],0)]);seen={f['start']};trace=[]
    while queue:
        node,path,cost=queue.popleft();trace.append(dict(event='pop',node=node,path=path,cost=cost,hops=len(path)-1))
        if node==f['goal']:return dict(path=path,cost=cost,hops=len(path)-1,trace=trace)
        for u,v,c in f['edges']:
            if u==node and v not in seen:
                seen.add(v);queue.append((v,path+[v],cost+c));trace.append(dict(event='enqueue',node=v,parent=node,cost=cost+c,hops=len(path)))
    return dict(path=None,cost=None,hops=None,trace=trace)

def priority_search(f,astar):
    h=f['h'] if astar else {n:0 for n in f['nodes']};serial=itertools.count();start=f['start'];front=[(h[start],next(serial),0,start,[start])];best={start:0};trace=[]
    while front:
        priority,order,g,node,path=heapq.heappop(front)
        if g!=best[node]:trace.append(dict(event='stale',node=node,cost=g,best=best[node]));continue
        trace.append(dict(event='pop',node=node,path=path,cost=g,h=h[node],priority=priority))
        if node==f['goal']:return dict(path=path,cost=g,hops=len(path)-1,trace=trace)
        for u,v,c in f['edges']:
            if u==node:
                candidate=g+c;improved=v not in best or candidate<best[v];trace.append(dict(event='relax',edge=[u,v,c],candidate=candidate,previous=best.get(v),improved=improved))
                if improved:
                    best[v]=candidate;heapq.heappush(front,(candidate+h[v],next(serial),candidate,v,path+[v]))
    return dict(path=None,cost=None,hops=None,trace=trace)

def run(f):
    reason=validate(f)
    if reason:return dict(status='INPUT_REJECTED',reason=reason,search_started=False,algorithms={})
    a={'bfs':bfs(f),'dijkstra':priority_search(f,False),'astar':priority_search(f,True)}
    reachable=a['dijkstra']['path'] is not None;bad=f['policy']=='bfs-is-mincost'
    return dict(status='BAD_ACCEPTED' if bad else 'COMPARED' if reachable else 'UNREACHABLE',search_started=True,algorithms=a,heuristic_checks=[dict(edge=[u,v,c],left=f['h'][u],right=c+f['h'][v],consistent=f['h'][u]<=c+f['h'][v]) for u,v,c in f['edges']],bad_judgment=dict(enabled=bad,claims_bfs_min_cost=bad,rule_failed=bad and a['bfs']['cost']!=a['dijkstra']['cost']))

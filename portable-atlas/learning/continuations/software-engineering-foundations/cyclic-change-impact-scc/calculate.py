import collections
def analyze(f):
    nodes=f['nodes'];edges=f['edges'];changed=f['changed']
    empty=dict(sccs=[],condensation_edges=[],cyclic_sccs=[],impacted_sccs=[],impacted_modules=[],selected_tests=[],missing_modules=[],selected_test_counts={},trace=[])
    if changed not in nodes or any(a not in nodes or b not in nodes for a,b in edges):return dict(empty,status='INPUT_REJECTED',reason='UNKNOWN_NODE')
    adjacency={n:[] for n in nodes}
    for a,b in edges:adjacency[a].append(b)
    index={};low={};stack=[];active=set();components=[];trace=[]
    def visit(v):
        index[v]=low[v]=len(index);stack.append(v);active.add(v);trace.append(dict(event='enter',node=v,index=index[v]))
        for w in adjacency[v]:
            if w not in index:visit(w);low[v]=min(low[v],low[w])
            elif w in active:low[v]=min(low[v],index[w]);trace.append(dict(event='active-edge',source=v,target=w))
        if low[v]==index[v]:
            group=[]
            while True:
                w=stack.pop();active.remove(w);group.append(w)
                if w==v:break
            components.append(sorted(group));trace.append(dict(event='component',members=sorted(group)))
    for n in nodes:
        if n not in index:visit(n)
    components.sort();owner={n:'+'.join(c) for c in components for n in c}
    dag=sorted({(owner[a],owner[b]) for a,b in edges if owner[a]!=owner[b]})
    reverse={'+'.join(c):[] for c in components}
    for a,b in dag:reverse[b].append(a)
    queue=collections.deque([owner[changed]]);seen=set()
    while queue:
        c=queue.popleft()
        if c in seen:continue
        seen.add(c);trace.append(dict(event='impact-component',component=c))
        queue.extend(reverse[c])
    affected=[c for c in components if '+'.join(c) in seen];impact=sorted(n for c in affected for n in c)
    cyclic=[c for c in components if len(c)>1 or (c[0],c[0]) in map(tuple,edges)]
    omit={n for c in cyclic for n in c} if f['mode']=='drop-cyclic' else set()
    selected=['T-'+n for n in impact if n not in omit];missing=sorted(n for n in impact if n in omit)
    return dict(status='BAD_SELECTION' if missing else 'ANALYZED',sccs=components,condensation_edges=[list(x) for x in dag],cyclic_sccs=cyclic,impacted_sccs=affected,impacted_modules=impact,selected_tests=selected,selected_test_counts={t:1 for t in selected},missing_modules=missing,trace=trace)

import re
MODES=('normal','missing-first-root')
def valid_id(value):
    if type(value) is not str or not re.fullmatch('[A-Z][A-Z0-9]{0,3}',value):raise ValueError('invalid object ID')
def validate(objects,roots,mode):
    if type(mode) is not str or mode not in MODES:raise ValueError('unknown mode')
    if type(objects) is not list or len(objects)>16:raise ValueError('0..16 objects required')
    ids=[];total=0
    for obj in objects:
        if type(obj) is not dict or set(obj)!={'id','refs'}:raise ValueError('exact id/refs object fields')
        valid_id(obj['id']);ids.append(obj['id'])
        refs=obj['refs']
        if type(refs) is not list or len(refs)>16:raise ValueError('refs list limit')
        for ref in refs:valid_id(ref)
        if len(set(refs))!=len(refs):raise ValueError('duplicate edge')
        total+=len(refs)
    if len(set(ids))!=len(ids):raise ValueError('duplicate object ID')
    if total>48:raise ValueError('48 edge limit')
    for obj in objects:
        if any(ref not in ids for ref in obj['refs']):raise ValueError('dangling input edge')
    if type(roots) is not list or len(roots)>16:raise ValueError('roots list limit')
    for root in roots:valid_id(root)
    if len(set(roots))!=len(roots):raise ValueError('duplicate root')
    if any(root not in ids for root in roots):raise ValueError('unknown root')

def collect(objects,roots,mode,mutant=None):
    validate(objects,roots,mode)
    ids=[obj['id'] for obj in objects]
    refs={obj['id']:obj['refs'][:] for obj in objects}
    adjacency={k:v[:] for k,v in refs.items()}
    if mutant=='reverse_edges':
        adjacency={k:[] for k in ids}
        for source,dests in refs.items():
            for dest in dests:adjacency[dest].append(source)
    marked,black,kept,freed=set(),set(),set(),set()
    queue=[];trace=[]
    def snapshot(phase,event,target=None,discovered=None):
        alive=[k for k in ids if k not in freed]
        edges=[[s,d] for s in alive for d in refs[s]]
        trace.append(dict(step=len(trace),phase=phase,event=event,target=target,discovered=discovered or [],
            queue=queue[:],marked=sorted(marked),gray=sorted(set(queue)),black=sorted(black),
            white=sorted(set(ids)-marked-freed),kept=sorted(kept),reclaimed=sorted(freed),heap_ids=alive,edges=edges))
    def discover(node):
        if node not in marked:marked.add(node);queue.append(node);return True
        return False
    snapshot('init','all white')
    omitted=roots[0] if mode=='missing-first-root' and roots else None
    for root in roots:
        if root==omitted:snapshot('mark','omit root',root)
        else:discover(root);snapshot('mark','seed root',root)
    if mutant=='retain_incoming':
        for dest in sorted({v for xs in refs.values() for v in xs}):discover(dest)
        snapshot('mark','incorrect incoming seeds')
    while queue:
        node=queue.pop(0);new=[]
        for ref in ([] if mutant=='skip_refs' else adjacency[node]):
            if discover(ref):new.append(ref)
        black.add(node);snapshot('mark','scan',node,new)
    pre_marked=sorted(marked)
    snapshot('mark-done','closure complete')
    if mutant=='clear_before_sweep':marked.clear();black.clear()
    for node in ids:
        retain=node in marked
        if mutant=='invert_sweep':retain=not retain
        if retain:
            kept.add(node)
            if mutant!='no_reset_keep':marked.discard(node);black.discard(node)
            snapshot('sweep','keep and reset mark',node)
        else:
            freed.add(node);marked.discard(node);black.discard(node)
            snapshot('sweep','reclaim',node)
    snapshot('complete','collection complete')
    edges=[[s,d] for s in ids if s in kept for d in refs[s]]
    return dict(mode=mode,declared_roots=roots[:],omitted_root=omitted,marked=pre_marked,
                survivors=sorted(kept),reclaimed=sorted(freed),remaining_edges=edges,
                dangling_roots=sorted(set(roots)-kept),dangling_edges=[e for e in edges if e[1] not in kept],
                mark_bits_after_gc=sorted(marked),steps=len(trace),trace=trace)

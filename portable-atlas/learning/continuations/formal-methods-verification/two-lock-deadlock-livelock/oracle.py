# SPDX-License-Identifier: Apache-2.0
"""Independent ownership/wait table and pairwise edge predicates; imports no producer."""
from itertools import product
def table(mode):
    firsts=[0,0] if mode=='same-order' else [0,1];pcs=range(5) if mode=='retry' else range(4);rows=[]
    for a,b in product(pcs,repeat=2):
        needs=[set() if pc in [0,3] else {firsts[p]} if pc in [1,4] else {0,1} for p,pc in enumerate([a,b])]
        if needs[0]&needs[1]:continue
        owners=[0 if lock in needs[0] else 1 if lock in needs[1] else -1 for lock in range(2)];waiting=[]
        for p,pc in enumerate([a,b]):waiting.append(firsts[p] if pc==0 else 1-firsts[p] if pc==1 else None)
        rows.append(dict(state=(a,b,*owners),waiting=waiting,holds=[sorted(n) for n in needs]))
    return rows

def edge(source,target,mode):
    changed=[p for p in range(2) if source[p]!=target[p]]
    if len(changed)!=1:return None
    p=changed[0];first=0 if p==0 or mode=='same-order' else 1;second=1-first;old,new=source[p],target[p];o=list(source[2:]);n=list(target[2:])
    if (old,new)==(0,1) and o[first]==-1 and n[first]==p and o[second]==n[second]:return (p,'acquire-first')
    if (old,new)==(1,2) and o[second]==-1 and n[second]==p and o[first]==n[first]:return (p,'acquire-second')
    if (old,new)==(2,3) and o==[p,p] and n==[-1,-1]:return (p,'complete-release')
    if mode=='retry' and (old,new)==(1,4) and o[second]==1-p and o==n:return (p,'observe-failure')
    if mode=='retry' and (old,new)==(4,0) and o[first]==p and n[first]==-1 and o[second]==n[second]:return (p,'release-retry')
    return None

def graph(mode):
    rows=table(mode);states=[r['state'] for r in rows];edges=[]
    for source in states:
        for target in states:
            result=edge(source,target,mode)
            if result:edges.append((source,target,*result))
    layers=[{(0,0,-1,-1)}];reached=set(layers[0]);distance={(0,0,-1,-1):0}
    while True:
        next_layer={e[1] for e in edges if e[0] in reached}-reached
        if not next_layer:break
        layers.append(next_layer)
        for s in next_layer:distance[s]=len(layers)-1
        reached|=next_layer
    return dict(rows=rows,reachable=reached,edges={e for e in edges if e[0] in reached},distance=distance)

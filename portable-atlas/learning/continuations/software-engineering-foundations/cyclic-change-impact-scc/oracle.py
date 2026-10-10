import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def inspect(case):return json.loads((ROOT/'hand-oracle.json').read_text())['cases'][case]
def independent(f):
    nodes=f['nodes'];edges=f['edges']
    if f['changed'] not in nodes or any(a not in nodes or b not in nodes for a,b in edges):return None
    reach={};paths={}
    for start in nodes:
        found=set();walks=[]
        def walk(path):
            found.add(path[-1]);walks.append(path[:])
            for a,b in edges:
                if a==path[-1] and b not in path:walk(path+[b])
        walk([start]);reach[start]=found;paths[start]=walks
    components=sorted({tuple(sorted(w for w in nodes if w in reach[v] and v in reach[w])) for v in nodes})
    impact=sorted(v for v in nodes if f['changed'] in reach[v])
    return dict(sccs=[list(c) for c in components],impacted_modules=impact,simple_paths=paths)

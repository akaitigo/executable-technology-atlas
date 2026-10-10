"""Independent exhaustive simple paths, <=5nodes, no queue/heap/relaxation."""
def all_paths(f,start=None):
    start=f['start'] if start is None else start;paths=[]
    def visit(path):
        if path[-1]==f['goal']:
            cost=sum(next(c for u,v,c in f['edges'] if u==a and v==b) for a,b in zip(path,path[1:]));paths.append(dict(path=path,cost=cost,hops=len(path)-1));return
        for u,v,c in f['edges']:
            if u==path[-1] and v not in path:visit(path+[v])
    visit([start]);return paths

def inspect(f):
    assert len(f['nodes'])<=5
    paths=all_paths(f);cost=min((p['cost'] for p in paths),default=None);hops=min((p['hops'] for p in paths),default=None)
    return dict(paths=paths,min_cost=cost,min_hops=hops,least_cost_paths=[p['path'] for p in paths if p['cost']==cost],distance_to_goal={n:min((p['cost'] for p in all_paths(f,n)),default=None) for n in f['nodes']})

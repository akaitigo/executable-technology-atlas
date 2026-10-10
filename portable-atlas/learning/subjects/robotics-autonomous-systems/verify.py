# SPDX-License-Identifier: Apache-2.0
"""Independent layer-BFS and integer orientation cell geometry. --record is explicit."""
import argparse,copy,hashlib,json,platform,random,re,sys
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
import robot,route
HERE=Path(__file__).resolve().parent
SOURCES=['robot.py','verify.py','route.py','serve.py','fixtures.json','oracle.json','index.html','README.md','VERIFICATION.md','coverage.json','sources.json','skills/atlas-robotics-autonomous-systems/SKILL.md']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def layer_bfs(w,h,start,goal,blocked):
    """Separate frontier propagation; does not call robot validator, BFS or geometry."""
    frontier={tuple(start)};seen=set(frontier);depth=0;blocked={tuple(p) for p in blocked}
    if tuple(goal) in blocked:return None
    while frontier:
        if tuple(goal) in frontier:return depth
        candidates=set()
        for x,y in frontier:
            for point in ((x,y+1),(x-1,y),(x,y-1),(x+1,y)):
                if 0<=point[0]<w and 0<=point[1]<h and point not in blocked and point not in seen:candidates.add(point)
        seen.update(candidates);frontier=candidates;depth+=1
        assert depth<=w*h
    return None


def geometry(a,b,cell):
    """Integer-scaled orientation/intersection, independent of slab clipping."""
    a=tuple(v*2 for v in a);b=tuple(v*2 for v in b);x,y=(v*2 for v in cell)
    corners=[(x-1,y-1),(x+1,y-1),(x+1,y+1),(x-1,y+1)]
    def inside(p):return x-1<=p[0]<=x+1 and y-1<=p[1]<=y+1
    def orient(p,q,r):return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    def on(p,q,r):return orient(p,q,r)==0 and min(p[0],q[0])<=r[0]<=max(p[0],q[0]) and min(p[1],q[1])<=r[1]<=max(p[1],q[1])
    def intersects(p,q,r,s):
        u,v,z,t=orient(p,q,r),orient(p,q,s),orient(r,s,p),orient(r,s,q)
        if (u>0>v or v>0>u) and (z>0>t or t>0>z):return True
        return on(p,q,r) or on(p,q,s) or on(r,s,p) or on(r,s,q)
    return inside(a) or inside(b) or any(intersects(a,b,corners[i],corners[(i+1)%4]) for i in range(4))


def path_check(f,plan):
    path=plan['path'];distance=layer_bfs(f['width'],f['height'],plan['start'],f['goal'],plan['obstacles'])
    assert len(plan['expanded'])<=f['width']*f['height'] and len({tuple(p) for p in plan['expanded']})==len(plan['expanded'])
    if distance is None:assert not path;return None
    assert path[0]==plan['start'] and path[-1]==f['goal'] and len(path)-1==distance
    for a,b in zip(path,path[1:]):
        assert abs(a[0]-b[0])+abs(a[1]-b[1])==1
        assert all(not geometry(a,b,c) for c in plan['obstacles'])
    return distance


def trace_check(f,result):
    previous=f['start'];moves=0;seen_observation=0
    for i,row in enumerate(result['trace']):
        assert row['index']==i and row['moves']<=f['move_budget']
        assert row['known_version']<=row['world_version']<=1
        if row['event']=='MOVE':
            moves+=1;a=row['details']['from_position'];b=row['position']
            assert a==previous and abs(a[0]-b[0])+abs(a[1]-b[1])==1
            assert all(not geometry(a,b,c) for c in row['world_obstacles'])
            previous=b
        elif row['event']=='OBSERVATION':
            seen_observation+=1;assert f['update']['after_moves']==moves
            assert row['details']['new_obstacle']==f['update']['cell'] and row['world_version']==1
            assert row['known_version']==(0 if result['policy']=='ignore-update' else 1)
        elif row['event']=='CHECK':
            target=row['details']['target']
            cells={tuple(c) for c in row['known_obstacles'] if geometry(previous,target,c)}
            assert cells=={tuple(hit['cell']) for hit in row['details']['known_contacts']}
        elif row['event']=='STOP_BEFORE':
            assert row['position']==previous
            assert any(geometry(previous,row['details']['target'],c) for c in row['known_obstacles'])
        elif row['event']=='COLLISION':
            assert row['position']==previous  # Simulated attempted contact, no move into blocked cell.
            assert any(geometry(previous,row['details']['target'],c) for c in row['world_obstacles'])
        assert row['moves']==moves and row['position']==previous
    assert seen_observation<=1 and moves==result['moves'] and previous==result['position']
    assert result['trace'][-1]['event']==result['status']
    assert len(result['trace'])<=2*f['move_budget']+9
    for plan in result['plans']:path_check(f,plan)


def execute():
    fixtures=json.loads((HERE/'fixtures.json').read_text());hand=json.loads((HERE/'oracle.json').read_text());runs=[]
    assert {f['id'] for f in fixtures}==set(hand['hand_cases'])
    for f in fixtures:
        expected=hand['hand_cases'][f['id']];straight=robot.naive(f)
        assert straight['status']==expected['naive']
        assert {tuple(c['cell']) for c in straight['contacts']}=={tuple(c) for c in f['obstacles'] if geometry(f['start'],f['goal'],c)}
        assert layer_bfs(f['width'],f['height'],f['start'],f['goal'],f['obstacles'])==expected['distance']
        outcomes={}
        for policy in ('replan','stop','ignore-update'):
            result=robot.execute(f,policy);trace_check(f,result)
            e=expected['policies'][policy] if 'policies' in expected else expected
            for k in ('status','moves','position'):assert result[k]==e[k],(f['id'],policy,k,result[k],e[k])
            if f['id']=='stale-obstacle' and policy=='replan':
                assert result['plans'][1]['start']==[2,2] and len(result['plans'][1]['path'])-1==6
                assert any(r['event']=='STOP_BEFORE' and r['position']==[2,2] for r in result['trace'])
            outcomes[policy]=result
        runs.append(dict(id=f['id'],input=f,naive=straight,independent_hand=expected,policies=outcomes))
    geometry_rows=[]
    for f in hand['geometry_cases']:
        oracle=geometry(f['a'],f['b'],f['cell']);actual=robot.segment_contact(f['a'],f['b'],f['cell'])
        assert oracle==f['hit']==(actual is not None);geometry_rows.append(dict(input=f,oracle_hit=oracle,slab_contact=actual))
    rng=random.Random(20261005);random_geometry=[]
    for _ in range(400):
        a=[rng.randrange(7),rng.randrange(7)];b=[rng.randrange(7),rng.randrange(7)];c=[rng.randrange(7),rng.randrange(7)]
        oracle=geometry(a,b,c);actual=robot.segment_contact(a,b,c)
        assert oracle==(actual is not None),(a,b,c)
        random_geometry.append(dict(a=a,b=b,cell=c,oracle_hit=oracle,slab_contact=actual))
    random_grids=[]
    for i in range(100):
        w,h=rng.randint(2,6),rng.randint(2,6);start=[0,0];goal=[w-1,h-1]
        blocked=[[x,y] for x in range(w) for y in range(h) if [x,y] not in [start,goal] and rng.random()<.3]
        f=dict(width=w,height=h,start=start,goal=goal,obstacles=blocked,move_budget=64)
        result=robot.execute(f);trace_check(f,result);distance=layer_bfs(w,h,start,goal,blocked)
        assert result['status']==('NO_PATH' if distance is None else 'REACHED')
        assert result['moves']==(0 if distance is None else distance)
        random_grids.append(dict(input=f,oracle_distance=distance,result=result))
    invalid=[];base=fixtures[1]
    changes=[('bool-width',dict(width=True)),('zero-height',dict(height=0)),('too-wide',dict(width=17)),('noninteger-start',dict(start=[.1,2])),('outside-goal',dict(goal=[7,2])),('blocked-start',dict(obstacles=[[0,2]])),('blocked-goal',dict(obstacles=[[6,2]])),('duplicate-obstacle',dict(obstacles=[[2,2],[2,2]])),('negative-budget',dict(move_budget=-1)),('bool-budget',dict(move_budget=True)),('over-budget',dict(move_budget=65)),('bool-update-tick',dict(update=dict(after_moves=True,cell=[3,2]))),('update-start',dict(update=dict(after_moves=0,cell=[0,2]))),('obstacles-type',dict(obstacles='wall'))]
    for name,change in changes:
        f=dict(base,**change)
        try:robot.execute(f)
        except ValueError as e:invalid.append(dict(id=name,input=f,error=str(e)))
        else:raise AssertionError(name)
    invalid_options=[]
    for name,f,policy in [('fixture-object',None,'replan'),('policy',base,'unknown')]:
        try:robot.execute(f,policy)
        except ValueError as e:invalid_options.append(dict(id=name,error=str(e)))
        else:raise AssertionError(name)
    return dict(version=robot.VERSION,seed=20261005,input_sha256=digest(HERE/'fixtures.json'),oracle_sha256=digest(HERE/'oracle.json'),runs=runs,geometry_cases=geometry_rows,random_geometry=random_geometry,random_grids=random_grids,invalid_inputs=invalid,invalid_options=invalid_options,author_routing_smoke={'collision':route.route('collision'),'real-robot':route.route('real-robot')},oracle_scope='Independent layer-BFS distance, integer orientation closed-cell geometry, handwritten case outcomes and per-move audit; no sensor or robotics benchmark')


def docs_check(record):
    planned={HERE/'observations/raw.json',HERE/'observations/receipt.json'}
    for f in ('README.md','skills/atlas-robotics-autonomous-systems/SKILL.md'):
        for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
            if not link.startswith(('https:','#')):
                p=((HERE/f).parent/link.split('#')[0]).resolve();assert p.exists() or (record and p in planned),link
    assert all(w in (HERE/'README.md').read_text() for w in ('前提','主要概念','実務判断','限界','原典','未教材'))
    coverage=json.loads((HERE/'coverage.json').read_text());sources=json.loads((HERE/'sources.json').read_text());ids={s['id'] for s in sources}
    assert 2<=len(coverage['next_experiments'])<=4
    for a in coverage['areas']+coverage['next_experiments']:assert a['source'] in ids and a['question']
    assert all(s in (HERE/'index.html').read_text() for s in ('coverage.json','sources.json','README.md'))
    assert route.route('collision')['status']=='supported' and route.route('real-robot')['status']=='unsupported'


def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
    data=execute();docs_check(args.record);sources={f:digest(HERE/f) for f in SOURCES};folder=HERE/'observations';qa=json.loads((folder/'ui-qa.json').read_text())
    if qa['status']=='passed':
        assert qa['observed_ui_sha256']==digest(HERE/'index.html')
        assert qa['observed_sources_sha256']==digest(HERE/'sources.json') and qa['observed_coverage_sha256']==digest(HERE/'coverage.json')
        matrix=json.loads((folder/'ui-matrix.json').read_text())['rows'];assert len(matrix)==30 and len({(r['id'],r['policy']) for r in matrix})==30
        for row in matrix:
            run=next(r for r in data['runs'] if r['id']==row['id']);result=run['policies'][row['policy']]
            for key in ('status','moves','position'):assert row[key]==result[key]
            assert row['naive_status']==run['naive']['status']
            assert row['initial_bfs_distance']==run['independent_hand']['distance'] and row['plans']==len(result['plans'])
            for key in ('known_version','world_version'):assert row[key]==result['trace'][-1][key]
    if args.record:
        (folder/'raw.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        names=['observations/raw.json','observations/ui-qa.json']
        for name in ('ui-matrix.json','preview-http.log','default-bind.txt','skill-smoke.json','iteration-failure.txt'):
            if (folder/name).exists():names.append('observations/'+name)
        receipt=dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py --record',environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),input_sha256=data['input_sha256'],sources=sources,artifacts={f:digest(HERE/f) for f in names},checks=dict(independent_oracle='passed',roadmap_local_links_sources='passed',author_smoke='passed; not independent AgentEval',actual_iab_qa=qa['status']))
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    else:
        receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==sources,'changed source requires explicit --record'
        assert receipt['input_sha256']==data['input_sha256']
        for f,h in receipt['artifacts'].items():assert digest(HERE/f)==h,f
        assert data==json.loads((folder/'raw.json').read_text())
        if qa.get('observed_raw_sha256'):assert qa['observed_raw_sha256']==digest(folder/'raw.json')
    print(json.dumps(dict(status='passed',record=args.record,fixtures=len(data['runs']),policies=3,random_grids=len(data['random_grids']),geometry_hand_cases=len(data['geometry_cases']),random_geometry=len(data['random_geometry']),invalid_inputs=len(data['invalid_inputs']),invalid_options=len(data['invalid_options']))))
if __name__=='__main__':main()

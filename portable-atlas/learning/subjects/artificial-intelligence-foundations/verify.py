# SPDX-License-Identifier: Apache-2.0
"""Read-only checker by default. --record explicitly refreshes original observations."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import re
import sys
sys.dont_write_bytecode = True
import search
import route

HERE = Path(__file__).resolve().parent
SOURCES = ['search.py', 'verify.py', 'cases.json', 'index.html', 'serve.py', 'README.md',
           'coverage.json', 'sources.json', 'VERIFICATION.md', 'skills/atlas-artificial-intelligence-foundations/SKILL.md', 'route.py']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle(grid, target=None):
    # Independent breadth-distance set closure; no production neighbors/solve/heuristic calls.
    w, h = grid['width'], grid['height']
    nodes = {(x, y) for x in range(w) for y in range(h)} - {tuple(p) for p in grid['blocked']}
    dist = {tuple(target or grid['goal']): 0}
    for depth in range(len(nodes)):
        new = {n for n in nodes - dist.keys() if any(abs(n[0]-q[0])+abs(n[1]-q[1]) == 1
                                                    for q in dist if dist[q] == depth)}
        dist.update({n: depth+1 for n in new})
        if not new:
            break
    return dist


def property_check(grid, mode):
    distances = oracle(grid)
    cells = [(x,y) for y in range(grid['height']) for x in range(grid['width']) if [x,y] not in grid['blocked']]
    values = {p: search.heuristic(p, tuple(grid['goal']), mode) for p in cells}
    over = [dict(cell=p, h=values[p], exact=distances[p]) for p in cells if p in distances and values[p] > distances[p]]
    inconsistent = [dict(edge=[p,q], h_from=values[p], h_to=values[q]) for p in cells for q in cells
                    if abs(p[0]-q[0])+abs(p[1]-q[1]) == 1 and values[p] > 1+values[q]]
    return dict(admissible=not over, consistent=not inconsistent, overestimates=over, violations=inconsistent)


def check_result(grid, result):
    exact = oracle(grid).get(tuple(grid['start']))
    path = result['path']
    if result['status'] == 'found':
        assert path[0] == tuple(grid['start']) and path[-1] == tuple(grid['goal'])
        assert len(path)-1 == result['cost']
        assert all(list(p) not in grid['blocked'] for p in path)
        assert all(abs(a[0]-b[0])+abs(a[1]-b[1]) == 1 for a,b in zip(path,path[1:]))
        assert result['cost'] >= exact
    else:
        assert exact is None and not path
    assert len(result['trace']) == result['expanded']
    for step in result['trace']:
        assert step['g']+step['h'] == step['f']
        assert step['selected_path'][0] == tuple(grid['start'])
        assert len(step['selected_path'])-1 == step['g']
        assert all(abs(a[0]-b[0])+abs(a[1]-b[1]) == 1 for a,b in zip(step['selected_path'],step['selected_path'][1:]))
        assert all(list(p) not in grid['blocked'] for p in step['selected_path'])
    return exact


def execute():
    grids = json.loads((HERE/'cases.json').read_text())
    specs = [ ('bfs', 'corridor', 'bfs','zero',True,'fifo'),
              ('manhattan','corridor','astar','manhattan',True,'fifo'),
              ('overestimate','corridor','astar','overestimate',True,'fifo'),
              ('reopen','corridor','astar','inconsistent',True,'fifo'),
              ('no-reopen','corridor','astar','inconsistent',False,'fifo'),
              ('tie-fifo','ties','astar','manhattan',True,'fifo'),
              ('tie-lifo','ties','astar','manhattan',True,'lifo'),
              ('unreachable','unreachable','astar','manhattan',True,'fifo'),
              ('same','same','astar','manhattan',True,'fifo') ]
    runs = []
    for name, case, alg, mode, reopen, tie in specs:
        grid = grids[case]
        result = search.solve(grid, alg, mode, reopen, tie)
        exact = check_result(grid, result)
        runs.append(dict(id=name, case=case, input=grid, options=dict(algorithm=alg, mode=mode,reopen=reopen,tie=tie),
                         oracle_cost=exact, heuristic=property_check(grid,mode), result=result))
    by = {r['id']:r for r in runs}
    assert [by[k]['result']['cost'] for k in ('bfs','manhattan','overestimate','reopen','no-reopen')] == [7,7,9,7,9]
    assert by['manhattan']['heuristic']['consistent'] and by['manhattan']['heuristic']['admissible']
    assert not by['overestimate']['heuristic']['admissible']
    assert by['reopen']['heuristic']['admissible'] and not by['reopen']['heuristic']['consistent']
    assert any(t['reopened'] for t in by['reopen']['result']['trace'])
    assert any(t['suppressed'] for t in by['no-reopen']['result']['trace'])
    assert by['tie-fifo']['result']['cost'] == by['tie-lifo']['result']['cost'] == 8
    assert by['tie-fifo']['result']['expanded'] > by['tie-lifo']['result']['expanded']
    # Seeded variations challenge algorithms independently of fixture expectations.
    rng = random.Random(20261005)
    for _ in range(120):
        grid = dict(width=4,height=4,start=[0,0],goal=[3,3],blocked=[])
        grid['blocked'] = [[x,y] for x in range(4) for y in range(4)
                           if (x,y) not in ((0,0),(3,3)) and rng.random() < .3]
        exact = oracle(grid).get((0,0))
        for alg, mode in [('bfs','zero'),('astar','manhattan')]:
            r = search.solve(grid,alg,mode)
            check_result(grid,r)
            assert r['cost'] == exact
    invalid = []
    base = grids['corridor']
    changes = [('width-zero', dict(width=0)), ('bool-dimension',dict(width=True)),
               ('outside',dict(start=[8,0])), ('blocked-start',dict(blocked=[[0,0]])),
               ('float-cell',dict(goal=[7.0,0])), ('bad-blocked',dict(blocked=None))]
    for name, change in changes:
        try:
            search.solve(dict(base,**change))
        except ValueError as e:
            invalid.append(dict(id=name,input=dict(base,**change),status='rejected',error=str(e)))
        else:
            raise AssertionError(name)
    invalid_options = []
    for options in [dict(algorithm='dfs'),dict(mode='unknown'),dict(tie='random'),dict(reopen=1),dict(algorithm='bfs',tie='lifo')]:
        try:
            search.solve(base,**options)
        except ValueError as e:
            invalid_options.append(dict(options=options,status='rejected',error=str(e)))
        else:
            raise AssertionError(options)
    return dict(model_version=search.VERSION, runs=runs, invalid=invalid, invalid_options=invalid_options, randomized_grids=120,
                oracle='independent distance-layer set closure; unit-cost four-neighbor edges',
                author_routing_smoke={'astar':route.route('astar'),'llm-training':route.route('llm-training')})


def docs_check(record=False):
    for f in ['README.md','skills/atlas-artificial-intelligence-foundations/SKILL.md']:
        for link in re.findall(r'\]\(([^)]+)\)', (HERE/f).read_text()):
            if not link.startswith(('https:', '#')):
                target = ((HERE/f).parent/link.split('#')[0]).resolve()
                planned = {HERE/'observations/raw.json', HERE/'observations/receipt.json'}
                assert target.exists() or (record and target in planned), link
    text = (HERE/'README.md').read_text()
    assert all(word in text for word in ['前提','主要概念','実務判断','限界','原典','未教材'])
    coverage = json.loads((HERE/'coverage.json').read_text())
    assert len(coverage['next_experiments']) == 4
    sources = json.loads((HERE/'sources.json').read_text())
    ids = {s['id'] for s in sources}
    for item in coverage['areas']:
        assert item['source'] in ids and item['question'] and item['concepts']
    html = (HERE/'index.html').read_text()
    assert 'coverage.json' in html and 'sources.json' in html and 'README.md' in html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    data = execute()
    assert route.route('astar')['status'] == 'supported'
    assert route.route('llm-training')['status'] == 'unsupported'
    docs_check(args.record)
    source_hashes = {f:digest(HERE/f) for f in SOURCES}
    raw = json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    folder = HERE/'observations'
    if args.record:
        (folder/'raw.json').write_text(raw)
        receipt = dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),
                       environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),
                       command='python3 verify.py --record', sources=source_hashes,
                       artifacts={name:digest(HERE/name) for name in ['observations/raw.json','observations/ui-qa.json','observations/preview-http.log']},
                       input_sha256=digest(HERE/'cases.json'),
                       checks={'runtime_oracle':'passed','roadmap_local_links_source_binding':'passed',
                               'author_routing_smoke':'passed; not independent AgentEval',
                               'actual_iab_qa':json.loads((folder/'ui-qa.json').read_text())['status']})
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    else:
        receipt = json.loads((folder/'receipt.json').read_text())
        assert receipt['sources'] == source_hashes, 'source changed: record explicitly after validation'
        for name, expected in receipt['artifacts'].items():
            assert expected == digest(HERE/name), 'artifact digest mismatch: '+name
        assert json.loads(raw) == json.loads((folder/'raw.json').read_text()), 'runtime replay differs'
    print(json.dumps(dict(status='passed',record=args.record,runs=len(data['runs']),invalid=len(data['invalid']),randomized_grids=120)))

if __name__ == '__main__':
    main()

# SPDX-License-Identifier: Apache-2.0
"""Finite unit-cost four-neighbor grid BFS / A*. No external dependencies."""
from collections import deque
import heapq

VERSION = 'grid-search-1'


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('grid must be an object')
    w, h = data.get('width'), data.get('height')
    if type(w) is not int or type(h) is not int or not (1 <= w <= 12 and 1 <= h <= 12):
        raise ValueError('width and height must be integers in 1..12')
    def cell(value):
        if not isinstance(value, (list, tuple)) or len(value) != 2 or any(type(x) is not int for x in value):
            raise ValueError('cell must be two integers')
        x, y = value
        if not (0 <= x < w and 0 <= y < h):
            raise ValueError('cell outside grid')
        return (x, y)
    start, goal = cell(data.get('start')), cell(data.get('goal'))
    if not isinstance(data.get('blocked'), list):
        raise ValueError('blocked must be an array')
    blocked = {cell(p) for p in data['blocked']}
    if start in blocked or goal in blocked:
        raise ValueError('start/goal is blocked')
    return w, h, start, goal, blocked


def neighbors(p, w, h, blocked):
    # Deterministic east, south, west, north order.
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        q = p[0]+dx, p[1]+dy
        if 0 <= q[0] < w and 0 <= q[1] < h and q not in blocked:
            yield q


def heuristic(p, goal, mode):
    if mode == 'manhattan':
        return abs(p[0]-goal[0]) + abs(p[1]-goal[1])
    if mode == 'zero':
        return 0
    if mode == 'overestimate':
        return 100 if p in ((1, 0), (2, 0)) else 0
    if mode == 'inconsistent':
        return { (1, 0): 6, (2, 0): 5 }.get(p, 0)
    raise ValueError('unsupported heuristic')


def solve(data, algorithm='astar', mode='manhattan', reopen=True, tie='fifo'):
    w, h, start, goal, blocked = validate(data)
    if algorithm not in ('bfs', 'astar') or tie not in ('fifo', 'lifo') or type(reopen) is not bool:
        raise ValueError('invalid search options')
    heuristic(start, goal, mode)  # Validate even when BFS ignores h.
    if algorithm == 'bfs' and tie != 'fifo':
        raise ValueError('BFS uses FIFO only')
    hfun = (lambda p: 0) if algorithm == 'bfs' else (lambda p: heuristic(p, goal, mode))
    best, parent, closed, trace = {start: 0}, {start: None}, set(), []
    queue, heap, serial = deque(), [], 0
    def push(p, g):
        nonlocal serial
        serial += 1
        if algorithm == 'bfs':
            queue.append((p, g, serial))
        else:
            heapq.heappush(heap, (g+hfun(p), serial if tie == 'fifo' else -serial, p, g, serial))
    def frontier():
        items = list(queue) if algorithm == 'bfs' else [(e[2], e[3], e[4]) for e in sorted(heap)]
        return [dict(cell=p, g=g, h=hfun(p), f=g+hfun(p), insertion=s) for p, g, s in items
                if best.get(p) == g and p not in closed]
    def path(p):
        out = []
        while p is not None:
            out.append(p)
            p = parent[p]
        return list(reversed(out))
    push(start, 0)
    while queue or heap:
        if algorithm == 'bfs':
            p, g, _ = queue.popleft()
        else:
            _, _, p, g, _ = heapq.heappop(heap)
        if best.get(p) != g or p in closed:
            continue
        closed.add(p)
        improvements, reopened, suppressed = [], [], []
        if p != goal:
            for q in neighbors(p, w, h, blocked):
                ng = g+1
                if ng >= best.get(q, float('inf')):
                    continue
                if q in closed:
                    if not reopen:
                        suppressed.append(dict(cell=q, old=best[q], candidate=ng))
                        continue
                    closed.remove(q)
                    reopened.append(dict(cell=q, old=best[q], new=ng))
                best[q], parent[q] = ng, p
                push(q, ng)
                improvements.append(dict(cell=q, g=ng))
        trace.append(dict(selected=p, g=g, h=hfun(p), f=g+hfun(p), closed=sorted(closed),
                          frontier=frontier(), improvements=improvements, reopened=reopened,
                          suppressed=suppressed, selected_path=path(p)))
        if p == goal:
            return dict(status='found', cost=g, path=path(p), trace=trace, expanded=len(trace))
    return dict(status='unreachable', cost=None, path=[], trace=trace, expanded=len(trace))

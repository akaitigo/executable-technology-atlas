"""Atlas: fixed four-variable binary CSP; no expected table import."""
from copy import deepcopy

VARIABLES = list('ABCD')
MODES = ('baseline', 'forward-checking', 'missing-restore')
METRICS = ('search_calls', 'candidate_attempts', 'assigned_constraint_tests',
           'consistency_rejections', 'propagation_tests', 'removed_values',
           'restored_values', 'domain_wipeouts', 'solutions')


def validate(problem, mode):
    if mode not in MODES:
        raise ValueError('unsupported mode')
    if not isinstance(problem, dict) or not isinstance(problem.get('id'), str):
        raise ValueError('problem object and ID required')
    domains = problem.get('initial_domains')
    if not isinstance(domains, dict) or sorted(domains) != VARIABLES:
        raise ValueError('exactly A B C D required')
    for values in domains.values():
        if (not isinstance(values, list) or not values or
                any(type(v) is not int or v not in (0, 1) for v in values) or values != sorted(set(values))):
            raise ValueError('initial domains must be nonempty ordered subsets of 0,1')
    edges = problem.get('edges')
    if not isinstance(edges, list) or len(edges) > 6:
        raise ValueError('at most six undirected edges')
    if any(not isinstance(e, list) or len(e) != 2 or any(v not in VARIABLES for v in e)
           or e[0] >= e[1] for e in edges):
        raise ValueError('normalized distinct endpoints required')
    if edges != [list(e) for e in sorted(set(map(tuple, edges)))]:
        raise ValueError('unique sorted edges required')


def solve(problem, mode):
    validate(problem, mode)
    domains = {v: set(problem['initial_domains'][v]) for v in VARIABLES}
    neighbors = {v: sorted(b if a == v else a for a, b in problem['edges'] if v in (a, b)) for v in VARIABLES}
    assignment, trail, solutions, events = {}, [], [], []
    metrics = dict.fromkeys(METRICS, 0)

    def record(action, depth, **detail):
        events.append({'seq': len(events), 'action': action, 'depth': depth,
                       'detail': deepcopy(detail), 'assignment': dict(assignment),
                       'domains': {v: sorted(domains[v]) for v in VARIABLES},
                       'trail': [list(p) for p in trail], 'metrics': dict(metrics),
                       'solutions': list(solutions)})

    def search(depth):
        metrics['search_calls'] += 1
        record('ENTER', depth)
        if depth == len(VARIABLES):
            solutions.append(''.join(str(assignment[v]) for v in VARIABLES))
            metrics['solutions'] += 1
            record('SOLUTION', depth, solution=solutions[-1])
            return
        v = VARIABLES[depth]
        candidates = sorted(domains[v])
        record('CANDIDATES', depth, variable=v, candidates=candidates)
        for color in candidates:
            metrics['candidate_attempts'] += 1
            record('TRY', depth, variable=v, color=color)
            ok = True
            for n in neighbors[v]:
                if n in assignment:
                    metrics['assigned_constraint_tests'] += 1
                    passes = color != assignment[n]
                    record('CHECK_ASSIGNED', depth, variable=v, color=color, neighbor=n, neighbor_value=assignment[n], passes=passes)
                    if not passes:
                        metrics['consistency_rejections'] += 1
                        ok = False
                        break
            if not ok:
                record('REJECT_CANDIDATE', depth, variable=v, color=color)
                continue
            mark = len(trail)
            assignment[v] = color
            record('ASSIGN', depth, variable=v, color=color, mark=mark)
            viable = True
            if mode != 'baseline':
                for n in neighbors[v]:
                    if n not in assignment:
                        for candidate in sorted(domains[n]):
                            metrics['propagation_tests'] += 1
                            passes = color != candidate
                            record('CHECK_FUTURE', depth, variable=v, color=color, neighbor=n, candidate=candidate, passes=passes)
                            if not passes:
                                domains[n].remove(candidate)
                                trail.append((n, candidate))
                                metrics['removed_values'] += 1
                                record('PRUNE', depth, variable=n, color=candidate, reason={'assigned_variable': v, 'assigned_color': color, 'edge': sorted([v, n])})
                        if not domains[n]:
                            metrics['domain_wipeouts'] += 1
                            record('WIPEOUT', depth, variable=n)
                            viable = False
                            break
            if viable:
                search(depth + 1)
            if mode == 'forward-checking':
                while len(trail) > mark:
                    n, candidate = trail.pop()
                    domains[n].add(candidate)
                    metrics['restored_values'] += 1
                    record('RESTORE', depth, variable=n, color=candidate, mark=mark)
            if mode == 'missing-restore':
                record('RESTORE_OMITTED', depth, mark=mark)
            del assignment[v]
            record('UNASSIGN', depth, variable=v, color=color)
        record('RETURN', depth)

    search(0)
    return {'id': problem['id'] + '--' + mode, 'problem': problem['id'], 'mode': mode,
            'solutions': solutions, 'metrics': metrics,
            'final_assignment': assignment, 'final_domains': {v: sorted(domains[v]) for v in VARIABLES},
            'final_trail': [list(p) for p in trail], 'events': events,
            'classification': 'design-counterexample' if mode == 'missing-restore' else ('all-solutions' if solutions else 'unsatisfiable'),
            'completed': True}

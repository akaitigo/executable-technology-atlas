"""Atlas: finite binary != propagation; no expected values or search oracle."""
from collections import deque
from copy import deepcopy

VARIABLES = tuple('ABCD')


def validate(case):
    domains = case['domains']
    if set(domains) != set(VARIABLES):
        raise ValueError('exactly four variables required')
    for values in domains.values():
        if not isinstance(values, list) or not values or any(type(x) is not int or x not in (0, 1) for x in values):
            raise ValueError('nonempty 0/1 integer domain required')
        if values != sorted(set(values)):
            raise ValueError('sorted unique domains required')
    edges = case['edges']
    if not isinstance(edges, list) or any(not isinstance(e, list) or len(e) != 2 or e[0] not in VARIABLES or e[1] not in VARIABLES or e[0] >= e[1] for e in edges):
        raise ValueError('normalized binary edge required')
    if edges != [list(e) for e in sorted(set(map(tuple, edges)))]:
        raise ValueError('sorted unique edges required')
    for variable, value in case['fixed_assignment'].items():
        if variable not in VARIABLES or type(value) is not int or domains[variable] != [value]:
            raise ValueError('fixed assignment must match singleton input')


def neighbors(edges):
    return {v: sorted(b if a == v else a for a, b in edges if v in (a, b)) for v in VARIABLES}


def forward_check(case):
    """One pass from given assignments, on its own copy, not recursive search."""
    validate(case)
    domains = deepcopy(case['domains'])
    fixed = case['fixed_assignment']
    adjacent = neighbors(case['edges'])
    metrics = dict(constraint_tests=0, removed_values=0, empty_domain_stops=0)
    events = []

    def record(action, **detail):
        events.append(deepcopy(dict(seq=len(events), action=action, detail=detail, domains=domains, metrics=metrics)))

    record('INITIAL')
    for a in sorted(fixed):
        for n in adjacent[a]:
            if n in fixed:
                continue
            for y in sorted(domains[n]):
                passes = fixed[a] != y
                metrics['constraint_tests'] += 1
                record('CHECK', assigned=a, value=fixed[a], neighbor=n, candidate=y, passes=passes)
                if not passes:
                    domains[n].remove(y)
                    metrics['removed_values'] += 1
                    record('REMOVE', variable=n, value=y, assigned=a, assigned_value=fixed[a])
            if not domains[n]:
                metrics['empty_domain_stops'] += 1
                record('EMPTY', variable=n)
                return dict(status='inconsistent', domains=domains, metrics=metrics, events=events)
    record('END')
    return dict(status='one-pass-complete', domains=domains, metrics=metrics, events=events)


def ac3(case):
    validate(case)
    domains = deepcopy(case['domains'])
    adjacent = neighbors(case['edges'])
    queue = deque(sorted((a, b) for edge in case['edges'] for a, b in (edge, edge[::-1])))
    queued = set(queue)
    metrics = dict(initial_arcs=len(queue), revise_calls=0, support_tests=0, removed_values=0,
                   queue_added=0, queue_skipped=0, empty_domain_stops=0)
    events, iterations = [], []

    def record(action, **detail):
        events.append(deepcopy(dict(seq=len(events), iteration=metrics['revise_calls'], action=action,
                                   detail=detail, domains=domains, queue=[list(a) for a in queue], metrics=metrics)))

    def result(status):
        return dict(status=status, domains=domains, remaining_queue=[list(a) for a in queue],
                    metrics=metrics, iterations=iterations, events=events)

    record('INITIAL')
    while queue:
        i, j = queue.popleft()
        queued.remove((i, j))
        metrics['revise_calls'] += 1
        record('POP', arc=[i, j])
        removed, added, skipped = [], [], []
        tests_before = metrics['support_tests']
        for x in sorted(domains[i]):
            supported = False
            for y in sorted(domains[j]):
                metrics['support_tests'] += 1
                supported = x != y
                record('SUPPORT_TEST', arc=[i, j], tail_value=x, head_value=y, passes=supported)
                if supported:
                    break
            if not supported:
                domains[i].remove(x)
                removed.append([i, x])
                metrics['removed_values'] += 1
                record('REMOVE', variable=i, value=x, head=j, head_domain=domains[j][:])
        record('REVISION_END', arc=[i, j], changed=bool(removed))
        if not domains[i]:
            metrics['empty_domain_stops'] += 1
            record('EMPTY', variable=i)
        elif removed:
            for k in adjacent[i]:
                if k == j:
                    continue
                arc = (k, i)
                if arc in queued:
                    metrics['queue_skipped'] += 1
                    skipped.append(list(arc))
                    record('ALREADY_QUEUED', arc=list(arc))
                else:
                    queue.append(arc)
                    queued.add(arc)
                    metrics['queue_added'] += 1
                    added.append(list(arc))
                    record('ENQUEUE', arc=list(arc))
        iterations.append(deepcopy(dict(arc=[i, j], domains_after=domains,
                            queue_after_iteration=[list(a) for a in queue], removed=removed,
                            enqueued=added, already_queued=skipped,
                            support_tests=metrics['support_tests'] - tests_before)))
        if not domains[i]:
            return result('inconsistent')
    record('END')
    return result('arc-consistent')


def compare(case):
    # Each algorithm receives the original input; each makes a separate copy.
    return dict(id=case['id'], FC=forward_check(case), AC3=ac3(case))

"""Atlas: finite synthetic-event reachability. No clock generator or transport."""
from collections import deque
from itertools import combinations


def base_edges(fixture):
    events = {e['id']: e for e in fixture['events']}
    if set(events) != set('abcdef') or len(fixture['events']) != 6:
        raise ValueError('fixed six distinct event IDs required')
    if any(type(e['clock']) is not int or e['clock'] < 0 for e in events.values()):
        raise ValueError('nonnegative integer labels required; bool excluded')
    if set(fixture['process_order']) != {'P', 'Q'}:
        raise ValueError('fixed two processes required')
    flat = [x for order in fixture['process_order'].values() for x in order]
    if len(flat) != 6 or set(flat) != set(events):
        raise ValueError('every event must belong to exactly one process sequence')
    edges = []
    for process, order in fixture['process_order'].items():
        if any(events[x]['process'] != process for x in order):
            raise ValueError('process membership mismatch')
        for a, b in zip(order, order[1:]):
            edges.append({'from': a, 'to': b, 'kind': 'process', 'source': process})
    if len(fixture['messages']) != 2 or {m['id'] for m in fixture['messages']} != {'m', 'n'}:
        raise ValueError('fixed complete message mapping required')
    endpoints = []
    for message in fixture['messages']:
        a, b = message['send'], message['receive']
        if a not in events or b not in events or events[a]['process'] == events[b]['process']:
            raise ValueError('message endpoints invalid')
        if events[a]['kind'] != 'send' or events[b]['kind'] != 'receive':
            raise ValueError('message direction invalid')
        if events[a]['message'] != message['id'] or events[b]['message'] != message['id']:
            raise ValueError('message identity mismatch')
        endpoints.extend([a, b])
        edges.append({'from': a, 'to': b, 'kind': 'message', 'source': message['id']})
    if len(set(endpoints)) != 4 or any(e['kind'] != 'local' or e['message'] is not None for k, e in events.items() if k not in endpoints):
        raise ValueError('unmapped or duplicate message event')
    if any(events[e['from']]['clock'] >= events[e['to']]['clock'] for e in edges):
        raise ValueError('fixed labels violate a supplied causal edge')
    for order in fixture['replays'].values():
        if len(order) != 6 or set(order) != set(events):
            raise ValueError('replay must contain each event exactly once')
        positions = {x: i for i, x in enumerate(order)}
        if any(positions[e['from']] >= positions[e['to']] for e in edges):
            raise ValueError('replay violates supplied causal edges')
    return edges


def reachable_paths(ids, edges):
    adjacency = {x: [] for x in ids}
    for edge in edges:
        adjacency[edge['from']].append(edge['to'])
    paths = {}
    for start in ids:
        queue = deque([[start]])
        discovered = {start}
        while queue:
            path = queue.popleft()
            for end in sorted(adjacency[path[-1]]):
                if end == start:
                    raise ValueError('cycle is outside the fixed acyclic model')
                if end not in discovered:
                    following = path + [end]
                    discovered.add(end)
                    paths[(start, end)] = following
                    queue.append(following)
    return paths


def relation(pairs, left, right):
    if (left, right) in pairs:
        return 'before'
    if (right, left) in pairs:
        return 'after'
    return 'concurrent'


def path_sources(path, edges):
    return [{'from': a, 'to': b, 'sources': [{'kind': e['kind'], 'source': e['source']} for e in edges
            if e['from'] == a and e['to'] == b]} for a, b in zip(path, path[1:])]


def compare(fixture, case):
    ids = sorted(e['id'] for e in fixture['events'])
    clocks = {e['id']: e['clock'] for e in fixture['events']}
    edges = base_edges(fixture)
    truth_paths = reachable_paths(ids, edges)
    truth = set(truth_paths)
    replay = fixture['replays'][case['replay']]
    used_edges = list(edges)
    if case['rule'] == 'causal':
        predicted_paths = truth_paths
    elif case['rule'] == 'scalar-inverse':
        used_edges = [{'from': a, 'to': b, 'kind': 'clock-inference', 'source': 'intentional-error'}
                      for a in ids for b in ids if clocks[a] < clocks[b]]
        predicted_paths = {(e['from'], e['to']): [e['from'], e['to']] for e in used_edges}
    elif case['rule'] == 'display-edges':
        used_edges += [{'from': a, 'to': b, 'kind': 'display-inference', 'source': case['replay']}
                       for a, b in zip(replay, replay[1:])]
        predicted_paths = reachable_paths(ids, used_edges)
    else:
        raise ValueError('unsupported finite comparison rule')
    predicted = set(predicted_paths)
    rows = []
    for a, b in combinations(ids, 2):
        actual = relation(truth, a, b)
        inferred = relation(predicted, a, b)
        true_direction = (a, b) if actual == 'before' else (b, a)
        inferred_direction = (a, b) if inferred == 'before' else (b, a)
        true_path = truth_paths.get(true_direction, []) if actual != 'concurrent' else []
        rule_path = predicted_paths.get(inferred_direction, []) if inferred != 'concurrent' else []
        rows.append({'left': a, 'right': b, 'causal_relation': actual, 'predicted_relation': inferred,
                     'causal_path': true_path, 'causal_path_edges': path_sources(true_path, edges),
                     'rule_path': rule_path, 'rule_path_edges': path_sources(rule_path, used_edges),
                     'matches': actual == inferred})
    false_positive = sorted(predicted - truth)
    false_negative = sorted(truth - predicted)
    return {'case_id': case['id'], 'rule': case['rule'], 'replay_id': case['replay'],
            'replay': list(replay), 'replay_clock_labels': [clocks[x] for x in replay],
            'clock_labels': clocks, 'events': fixture['events'], 'base_edges': edges, 'rule_edges': used_edges,
            'causal_pairs': [list(x) for x in sorted(truth)],
            'predicted_pairs': [list(x) for x in sorted(predicted)], 'pair_rows': rows,
            'predicted_causal_count': len(predicted), 'predicted_concurrent_count': len(rows) - len(predicted),
            'false_positive_pairs': [list(x) for x in false_positive],
            'false_negative_pairs': [list(x) for x in false_negative],
            'clock_condition_violations': [list(x) for x in sorted(truth) if clocks[x[0]] >= clocks[x[1]]],
            'classification': 'intentional-inference-counterexample' if false_positive or false_negative else 'matches-causal-relation',
            'scope': 'fixed six synthetic events; no physical-clock or transport measurement'}

"""Atlas: bounded independent teaching implementations, not Python's sort."""
from collections import Counter
from copy import deepcopy

METHODS = ('insertion', 'merge_left', 'merge_right')

def validate(records, method):
    if method not in METHODS:
        raise ValueError('invalid-method')
    if type(records) is not list or len(records) > 8:
        raise ValueError('invalid-input')
    ids = []
    for r in records:
        if type(r) is not dict or set(r) != {'key', 'id'}:
            raise ValueError('invalid-input')
        if type(r['key']) is not int or not -9 <= r['key'] <= 9:
            raise ValueError('invalid-input')
        if type(r['id']) is not str or len(r['id']) != 1 or not 'A' <= r['id'] <= 'Z':
            raise ValueError('invalid-input')
        ids.append(r['id'])
    if len(set(ids)) != len(ids):
        raise ValueError('invalid-input')

def sort_records(records, method):
    validate(records, method)
    events, frames = [], []
    comparisons = placements = 0
    def frame(label, start, items):
        frames.append({'label': label, 'scope': [start, start + len(items)],
                       'records': deepcopy(items), 'comparisons': comparisons, 'placements': placements})
    frame('入力（まだ整列していない）', 0, records)
    if method == 'insertion':
        result = deepcopy(records)
        for i in range(1, len(result)):
            held = result[i]
            j = i - 1
            events.append({'kind': 'hold', 'index': i, 'record': deepcopy(held)})
            while j >= 0:
                move = result[j]['key'] > held['key']
                comparisons += 1
                events.append({'kind': 'compare', 'left': deepcopy(result[j]), 'right': deepcopy(held), 'operator': '>', 'result': move})
                if not move:
                    break
                result[j + 1] = result[j]
                placements += 1
                events.append({'kind': 'place', 'reason': 'shift', 'index': j + 1, 'record': deepcopy(result[j])})
                j -= 1
            result[j + 1] = held
            placements += 1
            events.append({'kind': 'place', 'reason': 'held', 'index': j + 1, 'record': deepcopy(held)})
            frame('元位置' + str(i) + 'の要素を配置した後（後半は未整列）', 0, result)
    else:
        def merge(items, start):
            nonlocal comparisons, placements
            if len(items) < 2:
                return deepcopy(items)
            middle = len(items) // 2
            left, right = merge(items[:middle], start), merge(items[middle:], start + middle)
            out, i, j = [], 0, 0
            while i < len(left) and j < len(right):
                take_left = left[i]['key'] <= right[j]['key'] if method == 'merge_left' else left[i]['key'] < right[j]['key']
                comparisons += 1
                events.append({'kind': 'compare', 'scope': [start, start + len(items)], 'left': deepcopy(left[i]), 'right': deepcopy(right[j]), 'operator': '<=' if method == 'merge_left' else '<', 'result': take_left})
                chosen = left[i] if take_left else right[j]
                i += int(take_left)
                j += int(not take_left)
                out.append(chosen)
                placements += 1
                events.append({'kind': 'place', 'reason': 'merge', 'scope': [start, start + len(items)], 'index': len(out) - 1, 'record': deepcopy(chosen)})
            for remaining in (left[i:], right[j:]):
                for item in remaining:
                    out.append(item)
                    placements += 1
                    events.append({'kind': 'place', 'reason': 'remainder', 'scope': [start, start + len(items)], 'index': len(out) - 1, 'record': deepcopy(item)})
            frame('この範囲の併合が完了した部分列', start, out)
            return out
        result = merge(records, 0)
    # Diagnostics are separate from the comparisons used to sort.
    original_groups = {}
    output_groups = {}
    for r in records:
        original_groups.setdefault(r['key'], []).append(r['id'])
    for r in result:
        output_groups.setdefault(r['key'], []).append(r['id'])
    properties = {'sortedness': all(a['key'] <= b['key'] for a, b in zip(result, result[1:])),
                  'permutation': Counter((r['key'], r['id']) for r in result) == Counter((r['key'], r['id']) for r in records),
                  'stability': output_groups == original_groups}
    return {'method': method, 'output': result, 'comparisons': comparisons, 'placements': placements,
            'properties': properties, 'events': events, 'frames': frames}

def linear_membership(records, query):
    events = []
    for i, r in enumerate(records):
        found = r['key'] == query
        events.append({'index': i, 'key': r['key'], 'operator': '==', 'result': found})
        if found:
            return {'found': True, 'comparisons': len(events), 'events': events}
    return {'found': False, 'comparisons': len(events), 'events': events}

def binary_membership(records, query):
    lo, hi, events = 0, len(records), []
    while lo < hi:
        mid = (lo + hi) // 2
        less = records[mid]['key'] < query
        events.append({'lo': lo, 'hi': hi, 'index': mid, 'key': records[mid]['key'], 'operator': '<', 'result': less})
        if less:
            lo = mid + 1
        else:
            hi = mid
    found = False
    if lo < len(records):
        found = records[lo]['key'] == query
        events.append({'index': lo, 'key': records[lo]['key'], 'operator': '==', 'result': found})
    return {'found': found, 'comparisons': len(events), 'index': lo, 'events': events}

def compare_search(original, outcome, queries):
    rows, linear_total, binary_total = [], 0, 0
    for query in queries:
        linear = linear_membership(original, query)
        binary = binary_membership(outcome['output'], query)
        linear_total += linear['comparisons']
        binary_total += binary['comparisons']
        rows.append({'query': query, 'linear': linear, 'binary': binary,
                     'linearPrefix': linear_total, 'binaryPrefix': binary_total,
                     'preparedPrefix': outcome['comparisons'] + binary_total})
    return rows

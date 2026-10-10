"""Finite read-only cache model; no access to expected tables or host caches."""
from copy import deepcopy

MODES = ('direct', 'two-way-lru', 'two-way-no-hit-touch')


def validate(addresses, mode):
    if mode not in MODES:
        raise ValueError('unknown mode')
    if type(addresses) is not list or len(addresses) > 16:
        raise ValueError('addresses must be a list of at most 16 reads')
    if any(type(a) is not int or not 0 <= a <= 255 for a in addresses):
        raise ValueError('addresses must be exact integers 0..255')


def memory_byte(address):
    return (17 * address + 3) % 256


def simulate(addresses, mode):
    validate(addresses, mode)
    ways = 1 if mode == 'direct' else 2
    count = 4 // ways
    state = {
        'sets': [[{'valid': False, 'block': None, 'tag': None, 'bytes': []}
                  for _ in range(ways)] for _ in range(count)],
        'lru': [[] for _ in range(count)],
    }
    initial = deepcopy(state)
    events = []
    hits = misses = evictions = fetched_total = 0
    for number, address in enumerate(addresses, 1):
        before = deepcopy(state)
        block, offset = divmod(address, 4)
        tag, index = divmod(block, count)
        lines = state['sets'][index]
        selected = next((w for w, line in enumerate(lines)
                         if line['valid'] and line['tag'] == tag), None)
        hit = selected is not None
        victim = None
        fill_range = None
        if hit:
            hits += 1
            fetched = 0
            reason = 'valid-tag-hit'
        else:
            misses += 1
            selected = next((w for w, line in enumerate(lines) if not line['valid']), None)
            if selected is None:
                selected = state['lru'][index][0]
                victim = lines[selected]['block']
                evictions += 1
                reason = 'replace-lru'
            else:
                reason = 'fill-invalid'
            base = block * 4
            lines[selected] = {'valid': True, 'block': block, 'tag': tag,
                               'bytes': [memory_byte(base + j) for j in range(4)]}
            fill_range = [base, base + 3]
            fetched = 4
            fetched_total += fetched
        touched = not hit or mode != 'two-way-no-hit-touch'
        if touched:
            recency = state['lru'][index]
            if selected in recency:
                recency.remove(selected)
            recency.append(selected)
        returned = lines[selected]['bytes'][offset]
        events.append({
            'step': number, 'address': address, 'block': block, 'set': index,
            'tag': tag, 'offset': offset, 'hit': hit, 'way': selected,
            'victim_block': victim, 'decision': reason, 'recency_touched': touched,
            'fill_range': fill_range, 'returned_byte': returned, 'fetched_bytes': fetched,
            'before': before, 'after': deepcopy(state),
        })
    return {
        'mode': mode,
        'classification': 'intentional-lru-fault' if mode == 'two-way-no-hit-touch' else 'normal',
        'geometry': {'capacity_bytes': 16, 'line_bytes': 4, 'line_count': 4,
                     'set_count': count, 'ways': ways, 'offset_bits': 2,
                     'set_bits': 2 if ways == 1 else 1, 'tag_bits': 4 if ways == 1 else 5},
        'initial': initial, 'events': events, 'final': deepcopy(state),
        'summary': {'reads': len(addresses), 'hits': hits, 'misses': misses,
                    'evictions': evictions, 'fetched_bytes': fetched_total,
                    'hit_rate': hits / len(addresses) if addresses else None},
    }

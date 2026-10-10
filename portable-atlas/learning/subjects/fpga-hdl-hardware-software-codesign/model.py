"""Finite clocked model. Not an HDL scheduler or physical timing model."""
VARIANTS = ('sync', 'next-state-bug', 'async')

def validate(data):
    if type(data) is not dict or set(data) != {'events'}:
        raise ValueError('eventsだけを持つobjectが必要')
    events = data['events']
    if type(events) is not list or len(events) > 64:
        raise ValueError('eventsは0..64件のlist')
    last = -1
    for e in events:
        if type(e) is not dict or set(e) != {'t', 'edge', 'en', 'rst'}:
            raise ValueError('eventはt/edge/en/rstだけを持つobject')
        if type(e['t']) is not int or not 0 <= e['t'] <= 10000 or e['t'] <= last:
            raise ValueError('tは0..10000の厳密増加integer')
        if any(type(e[k]) is not int or e[k] not in (0, 1) for k in ('edge', 'en', 'rst')):
            raise ValueError('edge/en/rstはinteger 0/1（bool不可）')
        last = e['t']
    return events

def step(q, prev, event, variant='sync'):
    if variant not in VARIANTS:
        raise ValueError('未対応variant')
    edge, en, rst = event['edge'], event['en'], event['rst']
    if rst and (edge or variant == 'async'):
        return 0, 0
    if edge:
        next_q = (q + 1) & 3 if en else q
        # All RHS read the pre-edge snapshot. Bug intentionally uses next_q.
        return next_q, next_q if variant == 'next-state-bug' else q
    return q, prev

def simulate(data):
    events = validate(data)
    traces = {}
    for variant in VARIANTS:
        q = prev = 0  # explicit educational initial state, not FPGA power-up claim
        rows = []
        for event in events:
            before = [q, prev]
            q, prev = step(q, prev, event, variant)
            rows.append(dict(event, before=before, q=q, prev=prev))
        traces[variant] = rows
    return {'status': 'accepted', 'initial': [0, 0], 'traces': traces}

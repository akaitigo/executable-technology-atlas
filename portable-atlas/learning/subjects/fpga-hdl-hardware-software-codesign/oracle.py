"""Specification oracle: explicit table, no call to model.step or arithmetic increment."""
INCREMENT = {0: 1, 1: 2, 2: 3, 3: 0}

def transition(q, prev, e, asynchronous=False):
    if e['rst'] == 1 and (e['edge'] == 1 or asynchronous):
        return (0, 0)
    if e['edge'] == 0:
        return (q, prev)
    return (INCREMENT[q] if e['en'] == 1 else q, q)

def trace(events, asynchronous=False):
    state = (0, 0)
    result = []
    for e in events:
        state = transition(*state, e, asynchronous)
        result.append(list(state))
    return result

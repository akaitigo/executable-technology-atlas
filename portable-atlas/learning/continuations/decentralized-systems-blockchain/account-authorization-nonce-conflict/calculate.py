import copy
AUTH={'alice':'A','bob':'B'}
def calculate(f):
    state=dict(balances={'A':100,'B':50},nonces={'A':0,'B':0},accepted_ids=[]);rows=[]
    for tx in f['transactions']:
        before=copy.deepcopy(state);reason=None
        if tx['actor'] not in AUTH:reason='UNKNOWN_ACTOR'
        elif type(tx['nonce']) is not int or tx['nonce']<0:reason='INVALID_NONCE'
        elif type(tx['amount']) is not int or tx['amount']<=0:reason='INVALID_AMOUNT'
        elif tx['source'] not in state['balances'] or tx['destination'] not in state['balances']:reason='UNKNOWN_ACCOUNT'
        elif tx['id'] in state['accepted_ids']:reason='DUPLICATE_ID'
        elif f['mode']!='balance-only' and AUTH[tx['actor']]!=tx['source']:reason='UNAUTHORIZED'
        elif f['mode']!='ignore-nonce' and tx['nonce']!=state['nonces'][tx['source']]:reason='NONCE_CONFLICT'
        elif tx['amount']>state['balances'][tx['source']]:reason='INSUFFICIENT_BALANCE'
        auth_ok=AUTH.get(tx['actor'])==tx['source'];nonce_ok=type(tx['nonce']) is int and tx['nonce']==state['nonces'].get(tx['source'])
        bad=reason is None and (not auth_ok or not nonce_ok)
        accepted=reason is None
        if accepted:
            state['balances'][tx['source']]-=tx['amount'];state['balances'][tx['destination']]+=tx['amount'];state['nonces'][tx['source']]+=1;state['accepted_ids'].append(tx['id'])
        rows.append(dict(transaction=tx,before=before,decision='BAD_ACCEPT' if bad else reason or 'ACCEPT',accepted=accepted,after=copy.deepcopy(state),authorization_ok=auth_ok,nonce_matches=nonce_ok,bad=bad))
    return dict(status='BAD_ACCEPTED' if any(r['bad'] for r in rows) else 'MIXED_DECISIONS' if any(r['accepted'] for r in rows) and any(not r['accepted'] for r in rows) else 'ALL_ACCEPTED' if all(r['accepted'] for r in rows) else 'ALL_REJECTED',processing_started=True,rows=rows,final=state,authorization_table=AUTH,actor_trust='trusted synthetic fixture; no signature verification')

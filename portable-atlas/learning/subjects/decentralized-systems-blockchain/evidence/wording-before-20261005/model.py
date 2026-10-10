"""Task-owned synthetic hash chain. No consensus, signatures, assets or live chain."""
import copy,hashlib,json
GENESIS={'height':0,'previousHash':'0'*64,'tx':None,'balances':{'mock-a':100,'mock-b':50}}
CASES=['normal','all-spent','zero','negative','overspend','forged-balance','forged-conserving','tamper-hash','tamper-link','replay','unknown-account','boolean-amount']
def canonical(body):return json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def seal(body):return dict(copy.deepcopy(body),hash=digest(body))
def new_ledger():return [seal(GENESIS)]
def append(ledger,tx,claimed=None):
    # Return a new list; existing prefix is never changed. Caller supplies synthetic candidates.
    balances=dict(ledger[-1]['balances'])
    if claimed is None:
        balances[tx['sender']]-=tx['amount'];balances[tx['receiver']]+=tx['amount']
    else:balances=dict(claimed)
    body={'height':len(ledger),'previousHash':ledger[-1]['hash'],'tx':copy.deepcopy(tx),'balances':balances}
    return copy.deepcopy(ledger)+[seal(body)]
def candidate(case='normal',amount=10):
    if case not in CASES or type(amount) is not int or not 1<=amount<=100:raise ValueError('input')
    tx={'id':'t1','sender':'mock-a','receiver':'mock-b','amount':amount}
    ledger=new_ledger()
    if case=='all-spent':tx['amount']=100
    if case=='zero':tx['amount']=0
    if case=='negative':tx['amount']=-1
    if case=='overspend':tx['amount']=101
    if case=='unknown-account':tx['sender']='mock-z'
    if case=='boolean-amount':tx['amount']=True
    claimed={'mock-a':100,'mock-b':50} if case=='unknown-account' else None
    if case=='forged-balance':claimed={'mock-a':100,'mock-b':60}
    if case=='forged-conserving':claimed={'mock-a':95,'mock-b':55}
    ledger=append(ledger,tx,claimed)
    if case=='replay':ledger=append(ledger,tx)
    if case=='tamper-hash':ledger[1]['tx']['amount']=amount+1
    if case=='tamper-link':
        ledger[1]['previousHash']='f'*64
        ledger[1]=seal({k:v for k,v in ledger[1].items() if k!='hash'})
    return ledger

def chain_check(ledger):
    trace=[]
    if not isinstance(ledger,list) or not 1<=len(ledger)<=100:return {'result':'input','trace':trace}
    for i,block in enumerate(ledger):
        if not isinstance(block,dict) or set(block)!={'height','previousHash','tx','balances','hash'} or type(block['height']) is not int or block['height']!=i or not isinstance(block['hash'],str):return {'result':'input','trace':trace,'failedHeight':i}
        body={k:v for k,v in block.items() if k!='hash'}
        calculated=digest(body)
        parent='0'*64 if i==0 else ledger[i-1]['hash']
        entry={'height':i,'receivedHash':block['hash'],'computedHash':calculated,'expectedPreviousHash':parent,'receivedPreviousHash':block['previousHash'],'hashMatches':calculated==block['hash'],'linkMatches':parent==block['previousHash']}
        trace.append(entry)
        if not entry['hashMatches']:return {'result':'hash-mismatch','trace':trace,'failedHeight':i}
        if not entry['linkMatches']:return {'result':'link-mismatch','trace':trace,'failedHeight':i}
        if i==0 and canonical(body)!=canonical(GENESIS):return {'result':'genesis-mismatch','trace':trace,'failedHeight':i}
    return {'result':'accept','trace':trace}

def validate(ledger):
    chain=chain_check(ledger)
    state=dict(GENESIS['balances']);seen=set();decisions=[]
    if chain['result']!='accept':return {'result':chain['result'],'balances':state,'decisions':decisions,'chain':chain}
    for block in ledger[1:]:
        tx=block['tx'];reason=None
        if not isinstance(tx,dict) or set(tx)!={'id','sender','receiver','amount'} or not isinstance(tx['id'],str) or not 1<=len(tx['id'])<=32 or not isinstance(tx['sender'],str) or not isinstance(tx['receiver'],str) or type(tx['amount']) is not int:reason='input'
        elif tx['sender'] not in state or tx['receiver'] not in state:reason='unknown-account'
        elif tx['sender']==tx['receiver'] or tx['amount']<=0:reason='amount-rejected'
        elif tx['id'] in seen:reason='replay'
        elif tx['amount']>state[tx['sender']]:reason='insufficient-balance'
        expected=dict(state)
        if reason is None:
            expected[tx['sender']]-=tx['amount'];expected[tx['receiver']]+=tx['amount']
            claims=block['balances']
            if not isinstance(claims,dict) or set(claims)!=set(state) or any(type(v) is not int for v in claims.values()):reason='input'
            elif claims!=expected:reason='balance-mismatch'
        decisions.append({'height':block['height'],'tx':tx,'before':dict(state),'expected':expected,'claimed':block['balances'],'expectedTotal':sum(expected.values()),'result':reason or 'accept'})
        if reason:return {'result':reason,'failedHeight':block['height'],'balances':state,'decisions':decisions,'chain':chain}
        state=expected;seen.add(tx['id'])
    assert sum(state.values())==150
    return {'result':'accept','balances':state,'decisions':decisions,'chain':chain}

def experiment(case='normal',amount=10):
    ledger=candidate(case,amount)
    return {'input':{'case':case,'amount':amount},'ledger':ledger,'ledgerSha256':digest(ledger),'naiveChainOnly':chain_check(ledger),'fullValidation':validate(ledger)}


def validated_append(ledger,tx):
    if validate(ledger)['result']!='accept':raise ValueError('invalid existing prefix')
    proposed=append(ledger,tx)
    outcome=validate(proposed)
    if outcome['result']!='accept':raise ValueError(outcome['result'])
    return proposed

"""Independent traversal and hand balances; does not import model."""
import hashlib,json
HAND={'normal':('accept',{'mock-a':90,'mock-b':60}),'all-spent':('accept',{'mock-a':0,'mock-b':150}),'zero':('amount-rejected',{'mock-a':100,'mock-b':50}),'negative':('amount-rejected',{'mock-a':100,'mock-b':50}),'overspend':('insufficient-balance',{'mock-a':100,'mock-b':50}),'forged-balance':('balance-mismatch',{'mock-a':100,'mock-b':50}),'forged-conserving':('balance-mismatch',{'mock-a':100,'mock-b':50}),'tamper-hash':('hash-mismatch',{'mock-a':100,'mock-b':50}),'tamper-link':('link-mismatch',{'mock-a':100,'mock-b':50}),'replay':('replay',{'mock-a':90,'mock-b':60}),'unknown-account':('unknown-account',{'mock-a':100,'mock-b':50}),'boolean-amount':('input',{'mock-a':100,'mock-b':50})}
# Published SHA-256 known answer for ASCII abc, independent fixed constant.
ABC_SHA256='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
def traverse(blocks):
    initial={'mock-a':100,'mock-b':50}
    if not isinstance(blocks,list) or not blocks or len(blocks)>100:return {'result':'input','balances':initial}
    parent='0'*64
    for n,b in enumerate(blocks):
        if not isinstance(b,dict) or sorted(b)!=['balances','hash','height','previousHash','tx'] or isinstance(b['height'],bool) or b['height']!=n or not isinstance(b['height'],int) or not isinstance(b['hash'],str):return {'result':'input','balances':initial}
        body=dict(b);recorded=body.pop('hash');encoded=json.dumps(body,separators=(',',':'),sort_keys=True,ensure_ascii=True).encode('utf-8')
        if hashlib.sha256(encoded).hexdigest()!=recorded:return {'result':'hash-mismatch','balances':initial}
        if b['previousHash']!=parent:return {'result':'link-mismatch','balances':initial}
        if n==0 and encoded!=json.dumps({'height':0,'previousHash':'0'*64,'tx':None,'balances':initial},separators=(',',':'),sort_keys=True).encode():return {'result':'genesis-mismatch','balances':initial}
        parent=recorded
    # Independent arithmetic accumulated as debits/credits, with exact snapshot claims.
    movements={'mock-a':0,'mock-b':0};used=[]
    for b in blocks[1:]:
        current={k:initial[k]+movements[k] for k in initial};tx=b['tx'];reason=None
        if not isinstance(tx,dict) or sorted(tx)!=['amount','id','receiver','sender'] or not isinstance(tx['id'],str) or not 0<len(tx['id'])<=32 or not isinstance(tx['sender'],str) or not isinstance(tx['receiver'],str) or isinstance(tx['amount'],bool) or not isinstance(tx['amount'],int):reason='input'
        elif tx['sender'] not in initial or tx['receiver'] not in initial:reason='unknown-account'
        elif tx['sender']==tx['receiver'] or tx['amount']<1:reason='amount-rejected'
        elif tx['id'] in used:reason='replay'
        elif current[tx['sender']]<tx['amount']:reason='insufficient-balance'
        if reason:return {'result':reason,'balances':current}
        change=dict(movements);change[tx['sender']]-=tx['amount'];change[tx['receiver']]+=tx['amount']
        target={k:initial[k]+change[k] for k in initial}
        claims=b['balances']
        if not isinstance(claims,dict) or set(claims)!=set(initial) or any(isinstance(v,bool) or not isinstance(v,int) for v in claims.values()):return {'result':'input','balances':current}
        if any(claims[k]!=target[k] for k in initial):return {'result':'balance-mismatch','balances':current}
        movements=change;used.append(tx['id'])
    return {'result':'accept','balances':{k:initial[k]+movements[k] for k in initial}}

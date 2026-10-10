import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def inspect(c):return json.loads((ROOT/'hand-oracle.json').read_text())['cases'][c]
def utf8_hex(text):
    values=[]
    for c in text:
        n=ord(c)
        if n<128:values.append(n)
        elif n<2048:values.extend([192|(n>>6),128|(n&63)])
        elif n<65536:
            if 55296<=n<=57343:raise ValueError('surrogate outside contract')
            values.extend([224|(n>>12),128|((n>>6)&63),128|(n&63)])
        else:values.extend([240|(n>>18),128|((n>>12)&63),128|((n>>6)&63),128|(n&63)])
    return ''.join(format(n,'02x') for n in values)
def independent(f):
    old=dict(id='old',payload_hex='c3a9',bytes=2);rows=[old];status='REJECTED';reason=None;evicted=[];writes=0;accepted=False
    b=f['budget'];p=f['policy'];text=f['payload']
    if type(b) is not int:status='INPUT_REJECTED';reason='BUDGET_TYPE'
    elif b<0:status='INPUT_REJECTED';reason='BUDGET_RANGE'
    elif p not in ['RejectNew','OverwriteOldest','CharCountFault']:status='INPUT_REJECTED';reason='POLICY'
    elif not isinstance(text,str) or len(text)>16:status='INPUT_REJECTED';reason='INPUT_SIZE'
    elif not text:status='INPUT_REJECTED';reason='EMPTY_PAYLOAD'
    else:
        h=utf8_hex(text);n=len(h)//2
        if n>b:reason='SINGLE_PAYLOAD_EXCEEDS_BUDGET'
        elif p=='RejectNew' and n+2>b:reason='FULL'
        else:
            retain_old=(len(text)+1<=b) if p=='CharCountFault' else (n+2<=b)
            rows=([old] if retain_old else [])+[dict(id='new',payload_hex=h,bytes=n)]
            evicted=[] if retain_old else ['old'];writes=1 if retain_old else 2;accepted=True
            status='BAD_ACCEPTED' if sum(x['bytes'] for x in rows)>b else 'APPENDED' if retain_old else 'EVICTED'
    return dict(status=status,reason=reason,rows=rows,used_bytes=sum(x['bytes'] for x in rows),write_changes=writes,evicted=evicted,accepted=accepted)

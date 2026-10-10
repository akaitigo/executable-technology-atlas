import json,re,hmac,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
C=json.loads((ROOT/'contracts.json').read_text())
KEY=bytes.fromhex(C['public_fixture_key_hex'])
class Refusal(ValueError):pass
def pairs(items):
    d={}
    for k,v in items:
        if k in d:raise Refusal('duplicate-key')
        d[k]=v
    return d
def integer(s):
    if not re.fullmatch(r'0|[1-9][0-9]{0,2}',s):raise Refusal('number-spelling')
    return int(s)
def noninteger(s):raise Refusal('number-spelling')
def parse(s):
    try:d=json.loads(s,object_pairs_hook=pairs,parse_int=integer,parse_float=noninteger,parse_constant=noninteger)
    except Refusal:raise
    except (ValueError,TypeError):raise Refusal('json-syntax')
    if not isinstance(d,dict) or set(d)!=set(C['fields']):raise Refusal('field-set')
    if type(d['amount']) is not int:raise Refusal('amount-type')
    for field,values in C['strings'].items():
        if type(d[field]) is not str or d[field] not in values:raise Refusal('string-contract')
    return d
def encode(d,omit=None):return json.dumps({f:d[f] for f in C['fields'] if f!=omit},ensure_ascii=True,separators=(',',':')).encode('ascii')
def tag(b):return hmac.new(KEY,b,hashlib.sha256).hexdigest()
def trace(a,b):
    ta,tb=tag(a),tag(b)
    return {'left_ascii':a.decode('ascii'),'right_ascii':b.decode('ascii'),'left_hex':a.hex(),'right_hex':b.hex(),'left_tag':ta,'right_tag':tb,'bytes_equal':a==b,'tags_equal':ta==tb,'original_tag_verifies_changed':hmac.compare_digest(bytes.fromhex(ta),bytes.fromhex(tb))}
def execute():
    rows=[]
    for s in C['cases']:
        a,b=parse(s['left']),parse(s['right'])
        if s['mode']=='raw':good=trace(s['left'].encode('ascii'),s['right'].encode('ascii'))
        else:good=trace(encode(a),encode(b))
        row={'id':s['id'],'label':s['label'],'status':'accepted','mode':s['mode'],'input_left':s['left'],'input_right':s['right'],'normal':good}
        if s['mode']=='context':row['faulty']=trace(encode(a,s['omit']),encode(b,s['omit']));row['omitted']=s['omit']
        rows.append(row)
    for s in C['refusals']:
        try:parse(s['input'])
        except Refusal as e:rows.append({'id':s['id'],'label':s['label'],'status':'expected-refusal','input':s['input'],'reason':str(e),'tags_created':False})
        else:raise AssertionError('unexpected contract acceptance')
    return {'rows':rows,'public_key_hex':KEY.hex(),'claim':'finite byte contract only; no encryption, freshness, authorization or production security proof'}
if __name__=='__main__':print(json.dumps(execute(),ensure_ascii=False))

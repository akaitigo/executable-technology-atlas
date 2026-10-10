import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
C=json.loads((ROOT/'contracts.json').read_text())
class Refusal(ValueError):pass
def pairs(items):
    d={}
    for k,v in items:
        if k in d:raise Refusal('duplicate-key')
        d[k]=v
    return d
def parse(text):
    try:return json.loads(text,object_pairs_hook=pairs)
    except Refusal:raise
    except ValueError:raise Refusal('json-syntax')
def contract(text):
    d=parse(text)
    if type(d) is not dict or set(d)!= {'version','minimum','maximum','amount_type'}:raise Refusal('contract-fields')
    if d['version'] not in ('v1','v2') or d['amount_type']!='integer-not-bool':raise Refusal('contract-values')
    if type(d['minimum']) is not int or type(d['maximum']) is not int:raise Refusal('range-type')
    if not 0<=d['minimum']<=d['maximum']<=999:raise Refusal('range-order')
    return d
def source(text):
    d=parse(text)
    if type(d) is not list or len(d)!=1 or type(d[0]) is not dict or set(d[0])!={'id','amount'} or d[0]['id']!='r1':raise Refusal('source-fields')
    if type(d[0]['amount']) is not int:raise Refusal('amount-type')
    return d
def normalized(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def digest(v):return hashlib.sha256(v).hexdigest()
def validate(rows,rules):
    violations=[]
    for i,row in enumerate(rows,1):
        for rule,limit,test in (('minimum',rules['minimum'],row['amount']<rules['minimum']),('maximum',rules['maximum'],row['amount']>rules['maximum'])):
            if test:violations.append({'row':i,'column':'amount','rule':rule,'value':row['amount'],'limit':limit})
    return {'accepted':not violations,'violations':violations,'amount_sum':sum(r['amount'] for r in rows) if not violations else None}
def execute():
    rows=source(C['source_json']);base=contract(C['base_contract_json']);producer=digest((ROOT/'engine.py').read_bytes())
    oldbinding={'source':digest(normalized(rows)),'contract':digest(normalized(base)),'producer':producer};oldresult=validate(rows,base);cache={'binding':oldbinding,'result':oldresult};results=[]
    for s in C['cases']:
        current=contract(s['contract_json']);binding={'source':digest(normalized(rows)),'contract':digest(normalized(current)),'producer':producer};same=binding==oldbinding
        trace=[{'event':'binding-check','matches':same}]
        if same:normal={'cache_state':'reused','validation_state':'cache-reused-accepted',**copy.deepcopy(oldresult)};trace.append({'event':'cache-reuse'})
        else:
            trace.append({'event':'cache-invalidate','old_result_discarded':True});new=validate(rows,current);trace.append({'event':'revalidate','accepted':new['accepted'],'violations':new['violations']});normal={'cache_state':'invalidated','validation_state':'reevaluated-accepted' if new['accepted'] else 'reevaluated-rejected',**new}
        normal['trace']=trace
        faulty={'cache_state':'reused','validation_state':'cache-reused-accepted',**copy.deepcopy(oldresult),'trace':[{'event':'source-only-binding-check','matches':binding['source']==oldbinding['source']},{'event':'cache-reuse','contract_ignored':True}]}
        results.append({'id':s['id'],'label':s['label'],'status':'normal-comparison','current_contract_json':s['contract_json'],'current_contract':current,'binding':binding,'raw_contract_sha256':digest(s['contract_json'].encode()),'normalized_contract_ascii':normalized(current).decode(),'normalized_contract_sha256':binding['contract'],'raw_contract_equal':s['contract_json']==C['base_contract_json'],'normalized_contract_equal':same,'validation_semantics_equal':{k:v for k,v in current.items() if k!='version'}=={k:v for k,v in base.items() if k!='version'},'normal':normal,'faulty':faulty})
    for s in C['refusals']:
        try:
            current=contract(s['contract_json']);source(s['source_json'])
        except Refusal as e:results.append({'id':s['id'],'status':'expected-refusal','stage':s['stage'],'reason':str(e),'source_json':s['source_json'],'contract_json':s['contract_json'],'cache_used':False,'result_created':False})
        else:raise AssertionError('unexpected refusal acceptance')
    return {'rows':results,'initial_cache':cache,'base_contract_json':C['base_contract_json'],'base_raw_contract_sha256':digest(C['base_contract_json'].encode()),'source_json':C['source_json'],'claim':'independent custom JSON contract; not CSVW conformance, authenticity or business approval'}
if __name__=='__main__':print(json.dumps(execute(),ensure_ascii=False))

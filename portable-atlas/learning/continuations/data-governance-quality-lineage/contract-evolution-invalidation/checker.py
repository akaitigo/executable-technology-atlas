import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check_rows(raw,c,e):
    by={r['id']:r for r in raw['rows']};assert len(by)==len(raw['rows'])==9
    assert raw['source_json']==e['source_literal']=='[{"id":"r1","amount":100}]'
    source_hash=hashlib.sha256(b'[{"amount":100,"id":"r1"}]').hexdigest();base_literal=e['canonical_base_contract'];assert base_literal=='{"amount_type":"integer-not-bool","maximum":100,"minimum":0,"version":"v1"}'
    digest=lambda s:hashlib.sha256(s.encode()).hexdigest()
    old={'source':source_hash,'contract':digest(base_literal),'producer':sha(ROOT/'engine.py')};accepted={'accepted':True,'violations':[],'amount_sum':sum([100])}
    assert raw['initial_cache']=={'binding':old,'result':accepted} and raw['base_contract_json']==c['base_contract_json'] and raw['base_raw_contract_sha256']==digest(c['base_contract_json'])
    for s in c['cases']:
        r=by[s['id']];want=e['cases'][s['id']];assert r['status']=='normal-comparison' and r['current_contract_json']==s['contract_json'] and r['current_contract']==json.loads(s['contract_json'])
        literal=base_literal.replace('"maximum":100','"maximum":99') if s['id']=='max99' else base_literal.replace('"v1"','"v2"') if s['id']=='version-only' else base_literal
        binding={'source':source_hash,'contract':digest(literal),'producer':old['producer']}
        assert r['binding']==binding and r['normalized_contract_ascii']==literal and r['normalized_contract_sha256']==digest(literal) and r['raw_contract_sha256']==digest(s['contract_json'])
        assert r['raw_contract_equal']==want['raw_equal'] and r['normalized_contract_equal']==want['normalized_equal'] and r['validation_semantics_equal']==want['semantic_equal']
        normal=r['normal'];assert normal['cache_state']==want['cache_state'] and normal['validation_state']==want['validation_state'] and normal['violations']==want['violations'] and normal['amount_sum']==want['amount_sum'] and normal['accepted']==(want['amount_sum'] is not None)
        trace=[{'event':'binding-check','matches':want['normalized_equal']}]
        trace+= [{'event':'cache-reuse'}] if want['normalized_equal'] else [{'event':'cache-invalidate','old_result_discarded':True},{'event':'revalidate','accepted':normal['accepted'],'violations':want['violations']}]
        assert normal['trace']==trace
        assert r['faulty']=={'cache_state':'reused','validation_state':'cache-reused-accepted',**accepted,'trace':[{'event':'source-only-binding-check','matches':True},{'event':'cache-reuse','contract_ignored':True}]}
    for s in c['refusals']:assert by[s['id']]=={'id':s['id'],'status':'expected-refusal','stage':s['stage'],'reason':s['reason'],'source_json':s['source_json'],'contract_json':s['contract_json'],'cache_used':False,'result_created':False}
def main():
    raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.CONTRACT_OBSERVATION = ').strip().removesuffix(';'));d=ROOT/'observations'/raw['run_id'];assert json.loads((d/'raw.json').read_text())==raw
    for n,h in raw['source_digests'].items():assert sha(ROOT/n)==h,n
    for n,v in json.loads((d/'artifact-index.json').read_text())['artifacts'].items():assert sha(d/n)==v['sha256'] and (d/n).stat().st_size==v['bytes']
    c=json.loads((ROOT/'contracts.json').read_text());e=json.loads((ROOT/'expected-table.json').read_text())
    for n in ('contracts.json','expected-table.json'):assert (ROOT/n).read_bytes()==(d/n).read_bytes()
    cmd=json.loads((d/'command.json').read_text());assert cmd['exit']==0 and cmd['stderr']=='' and cmd['argv']==['python3','engine.py'] and json.loads(cmd['stdout'])['rows']==raw['rows']
    check_rows(raw,c,e);controls=[]
    for fault in ('stale-total-after-max99','version-means-rejection','format-means-rule-change','wrong-total','refusal-as-success'):
        bad=copy.deepcopy(raw)
        if fault=='stale-total-after-max99':bad['rows'][1]['normal']['amount_sum']=100
        if fault=='version-means-rejection':bad['rows'][2]['normal']['accepted']=False
        if fault=='format-means-rule-change':bad['rows'][3]['validation_semantics_equal']=False
        if fault=='wrong-total':bad['initial_cache']['result']['amount_sum']=99
        if fault=='refusal-as-success':bad['rows'][4]['status']='normal-comparison'
        try:check_rows(bad,c,e)
        except AssertionError:controls.append(fault)
        else:raise AssertionError('escaped '+fault)
    sys.dont_write_bytecode=True
    import route
    for q,t in route.ROUTES.items():assert route.route(q)=={'supported':True,'target':t,'executed':False,'reason':None}
    for q in route.UNSUPPORTED:assert route.route(q)['supported'] is False and route.route(q)['executed'] is False
    print(json.dumps({'status':'passed','run_id':raw['run_id'],'normal_comparisons':4,'expected_refusals':5,'independent_oracle':'handwritten violations/state table + fixed normalized literals + independent sum; no producer import','negative_controls_detected':controls,'skill_routes':{'normal':6,'unsupported':4,'scope':'structural only; model behavior unrun'}}))
if __name__=='__main__':main()

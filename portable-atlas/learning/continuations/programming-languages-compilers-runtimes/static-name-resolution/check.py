"""Read-only verifier; independent sequential environment lookup, no producer import."""
import copy,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
class Missing(Exception):
    pass
def lookup_program(ast):
    bindings={};pairs=[];failure=None
    def visit(block,parent):
        local={}
        def lookup(name):
            if name in local:return local[name]
            if parent:return parent(name)
            raise Missing()
        for node in block['body']:
            if node['kind']=='block':visit(node,lookup)
            elif node['kind']=='let':local[node['name']]=(node['id'],node['value'])
            else:
                try:decl,value=lookup(node['name'])
                except Missing:raise Missing(node)
                bindings[node['id']]=decl;pairs.append(dict(use=node['id'],decl=decl,value=value))
    try:visit(ast,None)
    except Missing as error:
        node=error.args[0];failure=dict(phase='resolution',reason='UNDECLARED',node=node['id'],name=node['name'])
    return bindings,pairs,failure
def verify(raw):
    fixtures=json.loads((ROOT/'fixtures.json').read_text());oracle=json.loads((ROOT/'oracle.json').read_text())
    assert set(raw)==set(fixtures)==set(oracle)
    for case,record in raw.items():
        assert record['case']==case and record['input']==fixtures[case]
        assert record['utc'].endswith('+00:00') and record['runtime']['python']
        assert record['source_binding']=={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('language.py','runner.py','fixtures.json','oracle.json')}
        r=record['result'];expected=oracle[case]
        for key,value in expected.items():assert r[key]==value,(case,key)
        correct,pairs,failure=lookup_program(fixtures[case]['ast'])
        binds=[e for e in r['resolution_trace'] if e['event']=='bind']
        assert {e['use']:e['decl'] for e in binds}==r['bindings'] and len(binds)==len(r['bindings'])
        if fixtures[case]['mode']=='strict':
            assert r['bindings']==correct and r['failure']==failure
            assert r['observations']==([] if failure else pairs)
        else:
            assert failure is None and r['bindings']!=correct
            assert r['observations']!=pairs
        assert r['values']==[p['value'] for p in r['observations']]
        uses=[];initialized={}
        for event in r['evaluation_trace']:
            if event['event']=='initialize':initialized[event['decl']]=event['value']
            if event['event']=='use':
                assert event['decl']==r['bindings'][event['use']]
                assert initialized[event['decl']]==event['value'];uses.append({k:event[k] for k in ('use','decl','value')})
        assert uses==r['observations']
        if not r['evaluation_started']:assert r['evaluation_trace']==[] and r['observations']==[]
        if case=='bad-pre-register':
            assert initialized=={'d-outer':10} and r['evaluation_trace'][-1]==dict(event='rejected',**r['failure'])
    return True
def main():
    raw=json.loads(sorted((ROOT/'observations').glob('*/raw.json'))[-1].read_text());verify(raw)
    mutations=[]
    def mutate(label,case,change):
        changed=copy.deepcopy(raw);change(changed[case]['result'])
        try:verify(changed)
        except (AssertionError,KeyError):mutations.append(label);return
        raise AssertionError('mutation escaped: '+label)
    mutate('wrong outer-after declaration','shadow',lambda r:r['bindings'].update({'u-after':'d-inner'}))
    mutate('wrong inner value','shadow',lambda r:r['values'].__setitem__(1,10))
    mutate('evaluation after scope refusal','scope-escape',lambda r:r.update(evaluation_started=True))
    mutate('wrong bad failure phase','bad-pre-register',lambda r:r['failure'].update(phase='resolution'))
    mutate('missing resolver bind event','sibling-scope',lambda r:r['resolution_trace'].__setitem__(slice(None),[e for e in r['resolution_trace'] if e.get('use')!='u-second']))
    print(json.dumps({'verified_cases':len(raw),'strict_completed':3,'strict_resolution_refusals':3,'bad_comparisons':2,'independent_environment_and_hand_oracle':True,'mutations_rejected':mutations},indent=2))
if __name__=='__main__':main()

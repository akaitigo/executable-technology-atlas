import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
C=json.loads((ROOT/'contracts.json').read_text())
FIELDS={'subject','authenticated_subject','scope','resource','action'}
def evaluate(request,mode,fixture_root):
    trace=[{'event':'request','mode':mode}];reads=0
    def result(decision,reason,content=None):
        return {'decision':decision,'reason':reason,'read_count':reads,'content_ascii':content.decode('ascii') if content is not None else None,'content_hex':content.hex() if content is not None else None,'content_sha256':hashlib.sha256(content).hexdigest() if content is not None else None,'trace':trace}
    def refuse(reason):
        trace.append({'event':'decision','decision':'refuse','reason':reason});return result('refuse',reason)
    if set(request)!=FIELDS:return refuse('request-field-set')
    if request['authenticated_subject'] is not True:return refuse('authenticated-subject-required')
    if type(request['subject']) is not str or request['subject'] not in C['subjects']:return refuse('subject-contract')
    if type(request['scope']) is not str or request['scope'] not in ('alpha','beta'):return refuse('scope-contract')
    if type(request['action']) is not str or request['action'] not in ('read','write'):return refuse('action-contract')
    if type(request['resource']) is not str or request['resource'] not in C['resources']:return refuse('unknown-resource')
    obj=C['resources'][request['resource']]
    if not all(type(obj.get(f)) is str for f in ('scope','owner','file')):return refuse('missing-resource-attribute')
    if obj['file'] not in ('alpha.txt','beta.txt'):return refuse('fixture-path-contract')
    subject=C['subjects'][request['subject']]
    trace.append({'event':'trusted-resource','resource':request['resource'],'scope':obj['scope'],'owner':obj['owner']})
    checks={'resource_scope_matches':request['scope']==obj['scope'],'subject_scope_assigned':request['scope']==subject['assigned_scope'],'read_permitted':request['action']=='read' and 'read' in subject['permissions']}
    trace.append({'event':'checks',**checks,'resource_scope_enforced':mode=='normal'})
    reason='allow'
    if mode=='normal' and not checks['resource_scope_matches']:reason='deny-resource-scope'
    elif not checks['subject_scope_assigned']:reason='deny-subject-scope'
    elif not checks['read_permitted']:reason='deny-read-permission'
    decision='allow' if reason=='allow' else 'deny';trace.append({'event':'decision','decision':decision,'reason':reason})
    if decision!='allow':return result(decision,reason)
    trace.append({'event':'read-start','fixture_file':obj['file']})
    # Actual IO only to the two filenames copied into owned dedicated directory.
    content=(fixture_root/obj['file']).read_bytes();reads+=1
    trace.append({'event':'read-complete','bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
    return result(decision,reason,content)
def run(fixture_root):
    rows=[]
    for req in C['cases']:
        request={k:v for k,v in req.items() if k!='id'}
        rows.append({'id':req['id'],'status':'normal-comparison','request':request,'normal':evaluate(request,'normal',fixture_root),'faulty':evaluate(request,'scope-only',fixture_root)})
    for s in C['refusals']:rows.append({'id':s['id'],'status':'expected-refusal','request':s['request'],'normal':evaluate(s['request'],'normal',fixture_root),'faulty':evaluate(s['request'],'scope-only',fixture_root)})
    return {'rows':rows,'identity':'authenticated_subject True is synthetic input assumption only','policy':'local finite subset, not NIST ABAC compliance','fixture_io':'two synthetic files in owned temporary directory; no user files/credentials'}
if __name__=='__main__':print(json.dumps(run(Path(sys.argv[1])),ensure_ascii=False))

"""Atlas: saved results checked against the pre-implementation handwritten table."""
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent

def verify(document):
    fixture=json.loads((BASE/'fixture.json').read_text())
    table=json.loads((BASE/'expected.json').read_text())
    extra=json.loads((BASE/'expected-addendum.json').read_text())
    checks=0
    def check(ok, message):
        nonlocal checks
        checks+=1
        if not ok: raise AssertionError(message)
    expected={}
    for role, allowed in table['roleFieldPermissions'].items():
        for obj, decision in table['defaultObjectJudgments'].items():
            expected[role+'/'+obj]=(role,obj,None,decision['status'],decision['reason'],False)
        for field in fixture['fields']:
            yes=field in allowed
            expected[role+'/field/'+field]=(role,'red-report',[field],200 if yes else 403,'ok' if yes else 'field-forbidden',False)
    for row in table['boundaryJudgments']:
        expected[row['id']]=('viewer','red-report',None,row['status'],row['reason'],False)
    expected['future-field']=('viewer','red-report',None,200,'ok',True)
    check(document['caseCount']==40 and len(document['cases'])==40,'case count')
    check(len({x['id'] for x in document['cases']})==40,'duplicate case')
    check(set(x['id'] for x in document['cases'])==set(expected),'exact case identities')
    counts={mode:0 for mode in ('object_only','projected')}
    for row in document['cases']:
        key=row['id']; role,obj,requested,status,reason,future=expected[key]
        check(row['inputsUnchanged'] is True,key+' inputs')
        full=dict(fixture['records'][obj])
        if future: full.update(extra['storeAddition'])
        for mode in counts:
            actual=row[mode]['response']
            wanted_status=status; wanted_reason=reason
            if mode=='object_only' and reason=='field-forbidden':wanted_status=200;wanted_reason='ok'
            wanted=None
            if wanted_status==200:
                if mode=='object_only':wanted=full
                else:
                    selected=table['roleFieldPermissions'][role] if requested is None else requested
                    wanted={k:full[k] for k in fixture['fields'] if k in selected}
                counts[mode]+=1
            check(actual=={'status':wanted_status,'reason':wanted_reason,'payload':wanted},key+' '+mode+' exact response')
            check((actual['payload'] is None)==(wanted_status!=200),key+' '+mode+' denial has no payload')
            if wanted is not None:check(list(actual['payload'])==list(wanted),key+' '+mode+' key order')
    check(counts=={'object_only':23,'projected':15},'permit totals')
    for name,digest in document['inputs'].items():
        check(hashlib.sha256((BASE/name).read_bytes()).hexdigest()==digest,name+' current')
        check(hashlib.sha256((BASE/'observations/run-01/inputs'/name).read_bytes()).hexdigest()==digest,name+' executed snapshot')
    return checks

def main():
    from copy import deepcopy
    data=json.loads((BASE/'observations/run-01/results.json').read_text())
    checks=verify(data); refused=[]
    for kind in ('missing-case','leaked-field','deny-payload'):
        bad=deepcopy(data)
        if kind=='missing-case':bad['cases'].pop()
        elif kind=='leaked-field':bad['cases'][0]['projected']['response']['payload']['internal_note']='架空の余分な値'
        else:bad['cases'][1]['projected']['response']['payload']={}
        try: verify(bad)
        except AssertionError:refused.append(kind)
        else:raise AssertionError('mutation not rejected: '+kind)
    print(json.dumps({'Atlas':'手書き許可表との全件照合','passed':True,'checks':checks,'cases':40,'mutationsRejected':refused},ensure_ascii=False))

if __name__=='__main__':main()

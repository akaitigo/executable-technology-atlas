"""Atlas: compare saved stores against the fixed handwritten changes table."""
import hashlib
import json
from pathlib import Path
from copy import deepcopy
BASE=Path(__file__).resolve().parent
def verify(data):
    fixture=json.loads((BASE/'fixture.json').read_text());cases=json.loads((BASE/'cases.json').read_text())['cases']
    expected=json.loads((BASE/'expected.json').read_text());expect={x['id']:x for x in expected['expected']};requests={x['id']:x for x in cases};checks=0
    def check(ok,message):
        nonlocal checks
        checks+=1
        if not ok:raise AssertionError(message)
    check(data['caseCount']==24 and len(data['cases'])==24,'case count')
    check(len({x['id'] for x in data['cases']})==24 and {x['id'] for x in data['cases']}==set(expect),'exact identities')
    counts={m:0 for m in expected['permitCounts']};denied_changed={m:[] for m in counts}
    for row in data['cases']:
        key=row['id'];case=requests[key];req=case['request'];before=fixture['records']
        check(row['context']==case['context'] and row['request']==req,key+' request/context')
        if isinstance(req.get('changes'),dict):check(list(row['request']['changes'])==list(req['changes']),key+' insertion order')
        check(row['beforeStore']==before,key+' initial whole store')
        check(set(row['outcomes'])==set(counts),key+' modes')
        for mode,decision in expect[key]['outcomes'].items():
            actual=row['outcomes'][mode];status=decision['status'];after=deepcopy(before)
            for f in decision['changedFields']:after[req['object_id']][f]=req['changes'][f]
            payload={'object_id':req['object_id'],'accepted_fields':list(req['changes'])} if status==200 else None
            check(actual['response']=={'status':status,'reason':decision['reason'],'payload':payload},key+' '+mode+' exact response')
            check(actual['afterStore']==after,key+' '+mode+' whole store')
            delta=[{'object_id':o,'field':f,'before':before[o][f],'after':after[o][f]} for o in before for f in before[o] if before[o][f]!=after[o][f]]
            check(actual['storeDelta']==delta,key+' '+mode+' exact delta')
            check(actual['contextUnchanged'] and actual['requestUnchanged'] and actual['fixtureUnchanged'],key+' '+mode+' read-only inputs')
            if status==200:counts[mode]+=1
            elif delta:denied_changed[mode].append(key)
    check(counts==expected['permitCounts'],'permit counts');check(denied_changed==expected['deniedStoreChanged'],'rejection side effects')
    for n,h in data['inputs'].items():
        check(hashlib.sha256((BASE/n).read_bytes()).hexdigest()==h,n+' current')
        check(hashlib.sha256((BASE/'observations/run-01/inputs'/n).read_bytes()).hexdigest()==h,n+' snapshot')
    return checks
def main():
    data=json.loads((BASE/'observations/run-01/results.json').read_text());count=verify(data);rejected=[]
    for name in ['missing-case','partial-write-on-deny','changed-other-record','false-success','denied-payload']:
        bad=deepcopy(data)
        if name=='missing-case':bad['cases'].pop()
        elif name=='partial-write-on-deny':bad['cases'][9]['outcomes']['validate_then_apply']['afterStore']['red-report']['title']='unwanted'
        elif name=='changed-other-record':bad['cases'][0]['outcomes']['validate_then_apply']['afterStore']['blue-report']['title']='unwanted'
        elif name=='false-success':bad['cases'][9]['outcomes']['validate_then_apply']['response']['status']=200
        else:bad['cases'][4]['outcomes']['validate_then_apply']['response']['payload']={}
        try:verify(bad)
        except AssertionError:rejected.append(name)
        else:raise AssertionError('mutation accepted '+name)
    print(json.dumps({'Atlas':'固定手表と全storeの照合','passed':True,'checks':count,'cases':24,'responses':72,'mutationsRejected':rejected},ensure_ascii=False))
if __name__=='__main__':main()

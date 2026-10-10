"""Atlas: read saved results against literal masses; no producer import."""
import copy
import datetime
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
SEQUENCES=['HHH','HHT','HTH','HTT','THH','THT','TTH','TTT']
MASSES=[[F(x,64) for x in [1,3,3,9,3,9,9,27]],[F(x,64) for x in [27,9,9,3,9,3,3,1]]]
def inspect(raw,spec,expected):
    count=0
    def ck(ok,label):
        nonlocal count
        if not ok:raise AssertionError(label)
        count+=1
    ck([x['id'] for x in raw['cases']]==[x['id'] for x in spec['cases']],'exact normal case set')
    ck([x['id'] for x in raw['refusals']]==[x['id'] for x in spec['refusals']],'exact refusal case set')
    for record,case,hand in zip(raw['cases'],spec['cases'],expected['cases']):
        ck(record['requestBefore']==record['requestAfter']==case['request'],'request binding '+case['id'])
        ck(record['outcome']['accepted'] is True and record['outcome']['reason']=='ok','normal status')
        p=record['outcome']['payload'];o=case['request']['observation'];w=case['request']['weights'];prior=[F(x,sum(w)) for x in w]
        n=len(o['value']) if o['type']=='sequence' else o['n'];k=o['value'].count('H') if o['type']=='sequence' else o['k']
        choose=[s.startswith(o['value']) if o['type']=='sequence' else s[:n].count('H')==k for s in SEQUENCES]
        likelihood=[sum((mass for mass,selected in zip(column,choose) if selected),F(0)) for column in MASSES]
        joint=[a*l for a,l in zip(prior,likelihood)];evidence=sum(joint,F(0));post=[x/evidence for x in joint]
        ck(p['hypotheses']==['1/4','3/4'] and p['n']==n and p['k']==k,'hypotheses/event binding')
        ck(p['multiplicity']==(3 if o['type']=='count' else 1),'finite multiplicity')
        for key,values in [('prior',prior),('likelihood',likelihood),('joint',joint),('posterior',post)]:
            ck(p[key]==[str(x) for x in values]==hand[key],key+' '+case['id'])
        ck(p['evidence']==str(evidence)==hand['evidence'],'evidence')
        ck(sum(F(x) for x in p['posterior'])==1,'posterior mass')
        for key in ('likelihoodAsPosterior','ignoresPrior'):ck(p['faults'][key]==hand[key],'fault '+key)
        ck(len(p['jointTable'])==8,'joint table length')
        for i,row in enumerate(p['jointTable']):
            ck(row['sequence']==SEQUENCES[i],'joint sequence')
            ck(row['inObservedEvent'] is choose[i],'observed membership')
            ck(row['conditionalMass']==[str(MASSES[j][i]) for j in range(2)],'conditional mass')
            ck(row['jointMass']==[str(prior[j]*MASSES[j][i]) for j in range(2)],'joint mass')
        ck(sum(F(x) for row in p['jointTable'] for x in row['jointMass'])==1,'whole joint sum')
    for record,case in zip(raw['refusals'],spec['refusals']):
        ck(record['requestBefore']==record['requestAfter']==case['request'],'refusal request')
        ck(record['outcome']=={'accepted':False,'reason':case['reason'],'payload':None},'refusal result')
    return count

raw=json.loads((BASE/'observations/run-01/results.json').read_text());spec=json.loads((BASE/'cases.json').read_text());expected=json.loads((BASE/'expected.json').read_text())
checks=inspect(raw,spec,expected);mutants=[]
for name in ('missing-case','ignored-prior','count-coefficient','joint-cell','refusal-payload','changed-request'):
    wrong=copy.deepcopy(raw)
    if name=='missing-case':wrong['cases'].pop()
    elif name=='ignored-prior':wrong['cases'][2]['outcome']['payload']['posterior']=['3/4','1/4']
    elif name=='count-coefficient':wrong['cases'][1]['outcome']['payload']['likelihood']=['9/64','3/64']
    elif name=='joint-cell':wrong['cases'][0]['outcome']['payload']['jointTable'][0]['jointMass'][0]='0'
    elif name=='refusal-payload':wrong['refusals'][0]['outcome']['payload']={}
    else:wrong['cases'][0]['requestAfter']['weights']=[1,3]
    try:inspect(wrong,spec,expected)
    except AssertionError:mutants.append(name)
    else:raise AssertionError('mutation accepted '+name)
for name,digest in raw['inputs'].items():
    assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==digest
    assert hashlib.sha256((BASE/'observations/run-01/inputs'/name).read_bytes()).hexdigest()==digest
    checks+=2
result={'Atlas':'有限Bayes保存照合','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':True,'checks':checks,'memoryMutationsRejected':mutants,'sourceBindings':raw['inputs'],'producerImported':False,'producerExecuted':False,'browserExecuted':False}
if '--record' in sys.argv:
    with (BASE/'verification/saved-result-check.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False))

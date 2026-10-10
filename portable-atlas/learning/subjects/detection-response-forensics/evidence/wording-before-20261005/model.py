"""Finite synthetic log detection. No accounts, host logs, network or attacks."""
import hashlib
import json
from pathlib import Path
FIXTURE = Path(__file__).resolve().parent/'fixtures.json'
def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def load_case(case):
    cases = json.loads(FIXTURE.read_text())
    if case not in cases: raise ValueError('input: unsupported fixed case')
    return cases[case]
def normalize(records):
    if not isinstance(records,list) or len(records)>100: raise ValueError('input')
    normalized=[]; decisions=[]; seen={}
    for i, row in enumerate(records):
        valid = isinstance(row,dict) and set(row)=={'id','user','time','action'}
        if valid:
            valid = isinstance(row['id'],str) and 1<=len(row['id'])<=32 and row['user'] in ('mock-a','mock-b') and type(row['time']) is int and 0<=row['time']<=1000 and row['action'] in ('fail','success')
        if not valid:
            decisions.append({'arrivalIndex':i,'status':'invalid-rejected','raw':row}); continue
        if row['id'] in seen:
            if row == seen[row['id']]:
                decisions.append({'arrivalIndex':i,'status':'duplicate-ignored','id':row['id']}); continue
            raise ValueError('input: conflicting duplicate id')
        seen[row['id']]=dict(row)
        normalized.append(dict(row,arrivalIndex=i))
        decisions.append({'arrivalIndex':i,'status':'accepted','id':row['id']})
    return normalized, decisions

def detect(records, mode='event-time', window=30, threshold=3):
    if mode not in ('event-time','arrival') or type(window) is not int or not 1<=window<=60 or type(threshold) is not int or not 1<=threshold<=10: raise ValueError('input')
    normalized, intake = normalize(records)
    ordered = sorted(normalized,key=lambda r:(r['time'],r['id'])) if mode=='event-time' else list(normalized)
    seen=[]; chain=[]; alerts=[]
    for row in ordered:
        if row['action']=='success':
            eligible=[f['id'] for f in seen if f['action']=='fail' and f['user']==row['user'] and row['time']-window<=f['time']<row['time']]
            alert=len(eligible)>=threshold
            chain.append({'id':row['id'],'time':row['time'],'stage':'success-evaluation','interval':[row['time']-window,row['time']],'intervalSemantics':'lower inclusive, upper exclusive','failureIds':eligible,'count':len(eligible),'threshold':threshold,'alert':alert})
            if alert: alerts.append(row['id'])
        else:
            chain.append({'id':row['id'],'time':row['time'],'stage':'failure-buffered'})
        seen.append(row)
    return {'mode':mode,'window':window,'threshold':threshold,'normalized':normalized,'normalization':intake,'processingOrder':[r['id'] for r in ordered],'decisionChain':chain,'alertIds':alerts,'normalizedSha256':digest(normalized),'decisionChainSha256':digest(chain)}

def experiment(case='late', mode='event-time', window=30, threshold=3):
    records=load_case(case)
    return {'input':{'case':case,'mode':mode,'window':window,'threshold':threshold},'rawInput':records,'fixtureFileSha256':hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),'inputSha256':digest(records),'selected':detect(records,mode,window,threshold),'arrival':detect(records,'arrival',window,threshold),'eventTime':detect(records,'event-time',window,threshold)}

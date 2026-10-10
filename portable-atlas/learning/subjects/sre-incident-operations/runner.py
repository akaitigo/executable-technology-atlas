"""Exact integer-rational arithmetic on synthetic events. Fixed toy SLO only."""
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def fixture():return json.loads((ROOT/'fixture.json').read_text())
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ratio(n,d):
    if d<=0:raise ValueError('zero-denominator')
    g=math.gcd(n,d);n//=g;d//=g
    return {'numerator':n,'denominator':d,'text':str(n)+'/'+str(d),'percentDisplay':f'{100*n/d:.3f}%'}
def validate(events):
    if not isinstance(events,list) or len(events)>100:raise ValueError('invalid-events')
    ids=set()
    for e in events:
        if not isinstance(e,dict) or set(e)!={'id','at','arrived','kind'}:raise ValueError('invalid-event-schema')
        if not isinstance(e['id'],str) or not e['id'] or e['id'] in ids:raise ValueError('duplicate-or-invalid-id')
        ids.add(e['id'])
        if type(e['at']) is not int or type(e['arrived']) is not int or not 0<=e['at']<=20 or e['arrived']<e['at']:raise ValueError('invalid-event-time')
        if e['arrived']>20:raise ValueError('late-input')
        if e['kind'] not in ('success','server_error','expected_rejection'):raise ValueError('unknown-outcome')
def calculate(events):
    validate(events)
    target={'numerator':9,'denominator':10};rows=[]
    for begin,end in [(0,10),(10,20)]:
        members=[e for e in events if begin<=e['at']<end]
        eligible=[e for e in members if e['kind']!='expected_rejection']
        n=len(eligible);good=sum(e['kind']=='success' for e in eligible);bad=n-good
        if n==0:raise ValueError('zero-events' if not events else 'zero-eligible-window')
        rows.append({'window':[begin,end],'allIds':[e['id'] for e in members],'eligibleIds':[e['id'] for e in eligible],'excludedIds':[e['id'] for e in members if e['kind']=='expected_rejection'],'good':good,'bad':bad,'denominator':n,'sli':ratio(good,n),'errorRate':ratio(bad,n),'allowedErrors':ratio(n,10),'remainingErrors':ratio(n-10*bad,10),'burnRate':ratio(bad*10,n)})
    good=sum(r['good'] for r in rows);bad=sum(r['bad'] for r in rows);n=sum(r['denominator'] for r in rows)
    a,b=rows
    naive=ratio(a['good']*b['denominator']+b['good']*a['denominator'],2*a['denominator']*b['denominator'])
    summary={'good':good,'bad':bad,'denominator':n,'excluded':sum(len(r['excludedIds']) for r in rows),'outsideIds':[e['id'] for e in events if e['at']==20],'sli':ratio(good,n),'errorRate':ratio(bad,n),'allowedErrors':ratio(n,10),'remainingErrors':ratio(n-10*bad,10),'burnRate':ratio(10*bad,n),'meetsToySLO':good*10>=9*n,'naiveUnweightedSLI':naive,'naiveMatches':naive['numerator']*n==good*naive['denominator']}
    return {'target':target,'windows':rows,'summary':summary}
def run(case='unequal-volume'):
    f=fixture()
    if case not in f['cases']:raise ValueError('unsupported-case')
    events=f['cases'][case]
    result={'case':case,'input':events,'inputDigest':digest(events),'model':'synthetic event arithmetic, fixed toy SLO90%; not operational recommendation or incident success','windowConvention':'[0,10), [10,20), watermark20; expected_rejection excluded from eligible population'}
    try:result.update(calculate(events))
    except ValueError as e:result['rejected']=str(e)
    return result
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--case',choices=list(fixture()['cases']),default='unequal-volume');a=p.parse_args();print(json.dumps(run(a.case),ensure_ascii=False,indent=2))

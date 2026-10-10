import argparse,datetime,hashlib,json,platform,time
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def load(n):return json.loads((ROOT/n).read_text())
def digest(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def ratio(x):return {'numerator':x.numerator,'denominator':x.denominator,'text':str(x)}
def validate(inp):
    if type(inp) is not dict or set(inp)!={'arrivals','service','window'}:raise ValueError('invalid-schema')
    a=inp['arrivals'];s=inp['service'];w=inp['window']
    if type(a) is not list or len(a)>20 or any(type(t) is not int or t<0 or t>100 for t in a) or a!=sorted(a):raise ValueError('invalid-arrivals')
    if type(s) is not int or not 1<=s<=10:raise ValueError('invalid-service')
    if type(w) is not list or len(w)!=2 or any(type(t) is not int for t in w) or not 0<=w[0]<w[1]<=200:raise ValueError('invalid-window')
def calculate(inp):
    validate(inp);a,b=inp['window'];T=b-a;jobs=[];free=0
    for i,arrival in enumerate(inp['arrivals']):
        start=max(arrival,free);finish=start+inp['service'];free=finish;jobs.append({'id':'j'+str(i+1),'arrival':arrival,'start':start,'finish':finish,'wait':start-arrival,'response':finish-arrival})
    points=sorted({a,b}|{t for j in jobs for t in (j['arrival'],j['start'],j['finish']) if a<t<b});segments=[]
    for left,right in zip(points,points[1:]):
        system=[j['id'] for j in jobs if j['arrival']<=left<j['finish']];queue=[j['id'] for j in jobs if j['arrival']<=left<j['start']];busy=[j['id'] for j in jobs if j['start']<=left<j['finish']]
        segments.append({'interval':[left,right],'systemIds':system,'queueIds':queue,'busyIds':busy,'systemArea':len(system)*(right-left),'queueArea':len(queue)*(right-left),'busyArea':len(busy)*(right-left)})
    area=sum(x['systemArea'] for x in segments);qa=sum(x['queueArea'] for x in segments);busy=sum(x['busyArea'] for x in segments)
    intersections=[]
    for j in jobs:
        residence=max(0,min(b,j['finish'])-max(a,j['arrival']));waiting=max(0,min(b,j['start'])-max(a,j['arrival']))
        intersections.append({'id':j['id'],'systemIntersection':residence,'queueIntersection':waiting})
    cohort=[x['id'] for x in intersections if x['systemIntersection']>0];completed=[j for j in jobs if a<j['finish']<=b];arrived=[j['id'] for j in jobs if a<=j['arrival']<b];carryIn=[j['id'] for j in jobs if j['arrival']<a<j['finish']];unfinished=[j['id'] for j in jobs if j['arrival']<b<j['finish']]
    L=Fraction(area,T);lambdaCompleted=Fraction(len(completed),T);lambdaArrival=Fraction(len(arrived),T);Wc=Fraction(sum(j['response'] for j in completed),len(completed)) if completed else None;Wq=Fraction(sum(j['wait'] for j in completed),len(completed)) if completed else None
    exposureMean=Fraction(area,len(cohort)) if cohort else None;cohortRate=Fraction(len(cohort),T);mixed=lambdaCompleted*Wc if Wc is not None else None
    return {'jobs':jobs,'segments':segments,'intersections':intersections,'window':inp['window'],'duration':T,'systemArea':area,'queueArea':qa,'busyArea':busy,'L':ratio(L),'Lq':ratio(Fraction(qa,T)),'utilization':ratio(Fraction(busy,T)),'arrivalIds':arrived,'completedIds':[j['id'] for j in completed],'carryInIds':carryIn,'unfinishedAtEndIds':unfinished,'cohortIds':cohort,'arrivalRate':ratio(lambdaArrival),'completionRate':ratio(lambdaCompleted),'completedMeanResponse':ratio(Wc) if Wc is not None else None,'completedMeanWait':ratio(Wq) if Wq is not None else None,'wrongCompletedProduct':ratio(mixed) if mixed is not None else None,'completedProductMatchesL':mixed==L if mixed is not None else None,'cohortExposureMean':ratio(exposureMean) if exposureMean is not None else None,'cohortRate':ratio(cohortRate),'finiteExposureProduct':ratio(cohortRate*exposureMean) if exposureMean is not None else None,'finiteIdentityDefined':bool(cohort),'scope':'finite batch FIFO, initially empty, no drop/buffer cap; model ticks not seconds; finite exposure identity is not steady-state performance guarantee'}
def run(case):
    cases=load('fixture.json')['cases']
    if case not in cases:raise ValueError('unsupported-case')
    inp=cases[case];start=time.perf_counter_ns()
    try:result=calculate(inp);status='calculated';reason=None
    except ValueError as e:result=None;status='rejected';reason=str(e)
    return {'case':case,'input':inp,'inputDigest':digest(inp),'status':status,'reason':reason,'result':result,'executedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executionObservedNs':time.perf_counter_ns()-start,'environment':{'python':platform.python_version(),'system':platform.system(),'machine':platform.machine()}}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',choices=list(load('fixture.json')['cases']),default='censored');a=p.parse_args();print(json.dumps(run(a.case),ensure_ascii=False,indent=2))

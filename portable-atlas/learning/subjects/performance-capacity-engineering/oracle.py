"""Independent hand timeline and unit-slot occupancy integration; no runner import."""
from fractions import Fraction
TIMES={'below-capacity':[(0,0,2),(3,3,5),(6,6,8)],'at-capacity':[(0,0,2),(2,2,4),(4,4,6),(6,6,8),(8,8,10)],'overload-drained':[(0,0,2),(1,2,4),(2,4,6),(3,6,8),(4,8,10)],'censored':[(0,0,2),(1,2,4),(2,4,6),(3,6,8),(4,8,10)],'cropped':[(0,0,2),(1,2,4),(2,4,6),(3,6,8),(4,8,10)],'arrival-at-end':[(0,0,2),(6,6,8)],'empty':[]}
WINDOWS={'below-capacity':(0,10),'at-capacity':(0,10),'overload-drained':(0,10),'censored':(0,6),'cropped':(2,6),'arrival-at-end':(0,6),'empty':(0,6)}
HAND={'below-capacity':(6,0,6),'at-capacity':(10,0,10),'overload-drained':(20,10,10),'censored':(14,8,6),'cropped':(11,7,4),'arrival-at-end':(2,0,2),'empty':(0,0,0)}
def f(v):return Fraction(v['numerator'],v['denominator'])
def audit(raw):
    case=raw['case']
    if case in ('invalid-service','invalid-window'):
        assert raw['status']=='rejected' and raw['reason']==case and raw['result'] is None;return {'validScenario':True,'status':'rejected','reason':case}
    assert raw['status']=='calculated' and raw['reason'] is None;r=raw['result'];times=TIMES[case];a,b=WINDOWS[case];assert r['window']==[a,b]
    jobs=[{'id':'j'+str(i+1),'arrival':arrival,'start':start,'finish':finish,'wait':start-arrival,'response':finish-arrival} for i,(arrival,start,finish) in enumerate(times)];assert r['jobs']==jobs
    # Independent slot count, not runner event-segment algorithm.
    system=queue=busy=0
    for t in range(a,b):
        system+=sum(arrival<=t<finish for arrival,start,finish in times);queue+=sum(arrival<=t<start for arrival,start,finish in times);busy+=sum(start<=t<finish for arrival,start,finish in times)
    assert (system,queue,busy)==HAND[case]==(r['systemArea'],r['queueArea'],r['busyArea'])
    for seg in r['segments']:
        l,u=seg['interval'];assert a<=l<u<=b
        ids=lambda fn:[j['id'] for j in jobs if fn(j,l)]
        assert seg['systemIds']==ids(lambda j,t:j['arrival']<=t<j['finish']);assert seg['queueIds']==ids(lambda j,t:j['arrival']<=t<j['start']);assert seg['busyIds']==ids(lambda j,t:j['start']<=t<j['finish'])
        for field,key in [('systemArea','systemIds'),('queueArea','queueIds'),('busyArea','busyIds')]:assert seg[field]==len(seg[key])*(u-l)
    assert sum(s['systemArea'] for s in r['segments'])==system and sum(s['queueArea'] for s in r['segments'])==queue and sum(s['busyArea'] for s in r['segments'])==busy
    assert r['segments'][0]['interval'][0]==a and r['segments'][-1]['interval'][1]==b and all(x['interval'][1]==y['interval'][0] for x,y in zip(r['segments'],r['segments'][1:]))
    intersections=[{'id':j['id'],'systemIntersection':sum(j['arrival']<=t<j['finish'] for t in range(a,b)),'queueIntersection':sum(j['arrival']<=t<j['start'] for t in range(a,b))} for j in jobs];assert r['intersections']==intersections and sum(x['systemIntersection'] for x in intersections)==system and sum(x['queueIntersection'] for x in intersections)==queue
    completed=[j for j in jobs if a<j['finish']<=b];cohort=[x['id'] for x in intersections if x['systemIntersection']];arrivals=[j['id'] for j in jobs if a<=j['arrival']<b]
    assert r['completedIds']==[j['id'] for j in completed] and r['cohortIds']==cohort and r['arrivalIds']==arrivals
    assert r['carryInIds']==[j['id'] for j in jobs if j['arrival']<a<j['finish']] and r['unfinishedAtEndIds']==[j['id'] for j in jobs if j['arrival']<b<j['finish']]
    assert f(r['L'])==Fraction(system,b-a) and f(r['Lq'])==Fraction(queue,b-a) and f(r['utilization'])==Fraction(busy,b-a)
    assert f(r['arrivalRate'])==Fraction(len(arrivals),b-a) and f(r['completionRate'])==Fraction(len(completed),b-a) and f(r['cohortRate'])==Fraction(len(cohort),b-a)
    if completed:
        mean=Fraction(sum(j['response'] for j in completed),len(completed));product=mean*Fraction(len(completed),b-a)
        assert f(r['completedMeanResponse'])==mean and f(r['completedMeanWait'])==Fraction(sum(j['wait'] for j in completed),len(completed)) and f(r['wrongCompletedProduct'])==product and r['completedProductMatchesL']==(product==Fraction(system,b-a))
    else:assert r['completedMeanResponse'] is r['completedMeanWait'] is r['wrongCompletedProduct'] is r['completedProductMatchesL'] is None
    assert r['finiteIdentityDefined']==bool(cohort)
    if cohort:assert f(r['cohortExposureMean'])==Fraction(system,len(cohort)) and f(r['finiteExposureProduct'])==Fraction(system,b-a)
    else:assert r['cohortExposureMean'] is r['finiteExposureProduct'] is None
    return {'validScenario':True,'status':'calculated','systemArea':system,'queueArea':queue,'L':str(Fraction(system,b-a)),'unfinished':r['unfinishedAtEndIds'],'carryIn':r['carryInIds'],'completedProductMatchesL':r['completedProductMatchesL']}

"""Independent fixed route tuples + Boolean equations, no runner/graph imports."""
from fractions import Fraction
ROUTES={'shared':[('app-a','dep-a',7),('app-b','dep-a',12)],'local':[('app-a','dep-a',7),('app-b','dep-b',7)],'replicated':[('app-a','dep-a',7),('app-a','dep-b',12),('app-b','dep-a',12),('app-b','dep-b',7)]}
ORDER=['zone-a','zone-b','app-a','app-b','dep-a','dep-b','router']
def check_result(r):
    bad=set(r['faults']);za='zone-a' not in bad;zb='zone-b' not in bad;a=za and 'app-a' not in bad;b=zb and 'app-b' not in bad;da=za and 'dep-a' not in bad;db=zb and 'dep-b' not in bad;router='router' not in bad
    health={'router':router,'app-a':a,'app-b':b,'dep-a':da,'dep-b':db};m=r['mode']
    success=router and ((a or b) and da if m=='shared' else (a and da) or (b and db) if m=='local' else (a or b) and (da or db))
    paths=[]
    for app,dep,cost in ROUTES[m]:
        ids=['router',app,dep];blocked=[n for n in ids if not health[n]];paths.append({'nodes':ids,'blockedNodes':blocked,'usable':not blocked,'latencySyntheticUnits':cost})
    usable=[p for p in paths if p['usable']];best=sorted(usable,key=lambda p:(p['latencySyntheticUnits'],p['nodes']))[0] if usable else None
    assert r['nodeHealth']==health and r['paths']==paths and r['serviceUp']==success
    assert r['selectedPath']==(best['nodes'] if best else None) and r['latencySyntheticUnits']==(best['latencySyntheticUnits'] if best else None)
    graph={'router':['app-a','app-b'],'app-a':[p[1] for p in ROUTES[m] if p[0]=='app-a'],'app-b':[p[1] for p in ROUTES[m] if p[0]=='app-b'],'dep-a':[],'dep-b':[]};assert r['graph']==graph
    return success
def audit(raw):
    if raw['case'] in ('unknown-fault','duplicate-fault'):
        assert raw['status']=='rejected' and raw['reason']==raw['case'] and raw['results']==[]
    else:assert raw['status']=='modeled' and raw['reason'] is None and [r['mode'] for r in raw['results']]==['shared','local','replicated'];[check_result(r) for r in raw['results']]
    return {'validScenario':True,'status':raw['status'],'serviceUp':{r['mode']:r['serviceUp'] for r in raw['results']},'latencySyntheticUnits':{r['mode']:r['latencySyntheticUnits'] for r in raw['results']},'reason':raw['reason']}
def audit_matrix(matrix):
    assert matrix['faultOrder']==ORDER and len(matrix['rows'])==128;sums={m:Fraction(0) for m in ROUTES};counts={m:0 for m in ROUTES};seen=set()
    for row in matrix['rows']:
        mask=row['mask'];assert mask not in seen and len(mask)==7 and set(mask)<={'0','1'};seen.add(mask);faults=[n for n,b in zip(ORDER,mask) if b=='1'];assert row['faults']==faults
        probability=Fraction(99,100)**mask.count('0')*Fraction(1,100)**mask.count('1');p=row['probabilityUnderAssumptions'];assert Fraction(p['numerator'],p['denominator'])==probability
        assert [r['mode'] for r in row['results']]==list(ROUTES)
        for r in row['results']:
            assert r['faults']==sorted(faults)
            if check_result(r):counts[r['mode']]+=1;sums[r['mode']]+=probability
    for m in ROUTES:
        v=matrix['modeledAvailability'][m];assert Fraction(v['numerator'],v['denominator'])==sums[m]
    assert counts==matrix['upStateCounts']=={'shared':10,'local':15,'replicated':17}
    q=Fraction(99,100);assert sums=={'shared':q**4+q**5-q**6,'local':2*q**4-q**7,'replicated':2*q**4+2*q**5-4*q**6+q**7}
    return {'states':128,'modeChecks':384,'counts':counts,'modeledFractions':{m:str(v) for m,v in sums.items()}}

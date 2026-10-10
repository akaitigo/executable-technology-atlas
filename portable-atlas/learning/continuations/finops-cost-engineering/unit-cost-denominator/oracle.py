"""Independent integer-pair and cross-product oracle; no producer imports."""
def reduced(n,d):
    if d==0:return None
    a,b=abs(n),abs(d)
    while b:a,b=b,a%b
    if d<0:n,d=-n,-d
    return [n//a,d//a]

def inspect(f):
    totals=[];attempts=[];success=[];unit=[];reported=[];denominators=[]
    for name in ['baseline','candidate']:
        p=f[name];total=0
        for row in p['costs']:total+=row['cents']
        totals.append(total);attempts.append(p['attempts']);success.append(p['success']);unit.append(reduced(total,p['success']))
        d=p['attempts'] if f['policy']=='all-attempts-as-success' else p['success'];denominators.append(d);reported.append(reduced(total,d))
    tr=reduced(totals[1],totals[0]);tc=reduced(totals[1]-totals[0],totals[0])
    def comparison(pair):
        a,b=pair
        if a is None or b is None or a[0]==0:return None,None
        return reduced(b[0]*a[1],b[1]*a[0]),reduced(b[0]*a[1]-b[1]*a[0],b[1]*a[0])
    ur,uc=comparison(reported);truth,_=comparison(unit)
    return dict(totals=totals,attempts=attempts,success=success,used_denominator=denominators,unit_cost=reported,strict_unit_cost=unit,total_ratio=tr,total_change=tc,unit_ratio=ur,unit_change=uc,strict_unit_ratio=truth)

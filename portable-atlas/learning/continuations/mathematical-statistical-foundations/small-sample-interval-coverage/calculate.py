"""Nine binomial terms + Decimal sqrt Wald bounds; no random source."""
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
from math import comb
from datetime import datetime,timezone
def utc():return datetime.now(timezone.utc).isoformat()
def calculate(data):
    result={'input':data,'started_at':utc(),'status':'refused','rows':None}
    reason=None
    if type(data.get('n')) is not int or data['n']!=8:reason='invalid-n'
    elif type(data.get('p')) is not str or data['p'] not in ('0.1','0.5','0.9'):reason='invalid-p'
    elif type(data.get('z')) is not str or data['z']!='1.96':reason='invalid-z'
    if reason:result.update(reason=reason,ended_at=utc());return result
    with localcontext() as ctx:
        ctx.prec=40;ctx.rounding=ROUND_HALF_EVEN
        n=8;p=Decimal(data['p']);z=Decimal(data['z']);rows=[]
        for k in range(9):
            estimate=Decimal(k)/n;variance=estimate*(1-estimate)/n;half=z*variance.sqrt()
            lower,upper=estimate-half,estimate+half
            mass=Decimal(comb(n,k))*p**k*(1-p)**(n-k)
            rows.append({'k':k,'estimate':str(estimate),'variance':str(variance),'lower':str(lower),'upper':str(upper),'width':str(2*half),'binomial_mass':str(mass),'covers_true_p':lower<=p<=upper,'outside_0_1':lower<0 or upper>1})
        result.update(status='calculated',rows=rows,context={'precision':40,'rounding':'ROUND_HALF_EVEN','critical':'1.96 rounded specified, not exact normal quantile','clipping':False},coverage=str(sum(Decimal(row['binomial_mass']) for row in rows if row['covers_true_p'])),probability_sum=str(sum(Decimal(row['binomial_mass']) for row in rows)),method='9 binomial terms; Decimal sqrt, theoretical calculation',ended_at=utc())
    return result
if __name__=='__main__':
    import json
    from pathlib import Path
    contract=json.loads(Path(__file__).with_name('contracts.json').read_text())
    print(json.dumps({'accepted':[calculate(data) for data in contract['accepted']],'refused':[calculate(item['input']) for item in contract['refusals']]},ensure_ascii=False))

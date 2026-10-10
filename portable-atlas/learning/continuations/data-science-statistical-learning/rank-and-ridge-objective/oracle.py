# SPDX-License-Identifier: Apache-2.0
from fractions import Fraction as F
# Closed forms and objective expansion; never imports model or its elimination.
def evaluate(c,w):
 w=[F(v) for v in w];x=c['X'];y=c['y'];pred=[];res=[]
 for i in range(len(y)):
  p=F(x[i][0])*w[0]+F(x[i][1])*w[1];pred.append(str(p));res.append(str(F(y[i])-p))
 rss=sum(F(v)**2 for v in res);norm=w[0]**2+w[1]**2;penalty=c['lambda_value']*norm
 return dict(predicted=pred,residuals=res,rss=str(rss),norm=str(norm),penalty=str(penalty),objective=str(rss+penalty))
def closed(c):
 l=F(c['lambda_value'])
 if c['id'].startswith('independent'):return [F(2)/(1+l),F(3)/(1+l)]
 if l:return [F(10)/(10+l),F(10)/(10+l)]
 return [F(2),F(0)]
def check(c,r,hand):
 name=c['id']
 if name in ('negative-lambda','wrong-shape'):
  assert r['status']=='REFUSED_INPUT' and r['solution'] is None;return True
 if name=='execution-failure':
  assert r['status']=='EXECUTION_FAILURE' and r['solution'] is None and 'ZeroDivisionError' in r['reason'];return True
 h=hand['solutions'][name];s=r['solution'];v=hand['independent' if name.startswith('independent') else 'correlated'];l=c['lambda_value']
 assert c['X']==v['X'] and c['y']==v['y'] and r['status']==h['status']
 assert s['rank_x']==v['rank'] and s['rank_system']==(2 if l or v['rank']==2 else 1)
 assert s['gram']==[[str(q) for q in row] for row in v['gram']] and s['rhs']==list(map(str,v['rhs']))
 assert s['system']==[[str(v['gram'][i][j]+(l if i==j else 0)) for j in range(2)] for i in range(2)]
 assert s['det']==h['det'] and s['coef']==list(map(str,closed(c)))
 assert s['null_basis']==h.get('null_basis',[])
 for k,value in evaluate(c,s['coef']).items():assert s[k]==value
 for k in ('rss','objective'):assert s[k]==h[k]
 if 'norm' in h:assert s['norm']==h['norm']
 for i in range(2):assert sum(F(s['system'][i][j])*F(s['coef'][j]) for j in range(2))==v['rhs'][i]
 if name=='correlated-ols':assert [x['coef'] for x in s['witnesses']]==hand['ols_family_samples']
 else:assert len(s['witnesses'])==1 and s['witnesses'][0]['coef']==s['coef']
 for witness in s['witnesses']:
  for k,value in evaluate(c,witness['coef']).items():assert witness[k]==value
  assert witness['objective']==s['objective']
 return True
def check_candidate(c,w,result):
 assert result==evaluate(c,w)
 optimum=closed(c);d1=F(w[0])-optimum[0];d2=F(w[1])-optimum[1]
 if c['id']=='independent-ols':gap=d1*d1+d2*d2
 elif c['id']=='independent-ridge':gap=2*(d1*d1+d2*d2)
 elif c['id']=='correlated-ols':gap=5*(d1+d2)**2
 else:gap=5*(d1+d2)**2+d1*d1+d2*d2
 assert F(result['objective'])-F(evaluate(c,optimum)['objective'])==gap and gap>=0
 return True

"""Receiverから独立したnormal equations / energy identity。正解はharnessだけ。"""
import json,sys
from fractions import Fraction as F

def pairs(x):return [tuple(F(c) for c in p) for p in x]
def enc(x):return [str(c) for c in x]
def expected(inp):
 p=pairs(inp['known_pilot']);r=pairs(inp['pilot_rx']);x=pairs(inp['payload_rx']);ek=sum(a*a+b*b for a,b in p);er=sum(a*a+b*b for a,b in r)
 corr=[(a*c+b*d,a*d-b*c) for (a,b),(c,d) in zip(p,r)];num=(sum(a for a,b in corr),sum(b for a,b in corr));h=(num[0]/ek,num[1]/ek) if ek else None;h2=sum(c*c for c in h) if h else None
 # 最小二乗のenergy恒等式でproducerの残差加算とは独立に総SSEを求める。
 sse=er-h2*ek if h else None;nr=sse/er if er and sse is not None else None
 rows=[]
 for i,((a,b),(c,d)) in enumerate(zip(p,r)):
  fit=(a*h[0]-b*h[1],b*h[0]+a*h[1]) if h else None;res=(c-fit[0],d-fit[1]) if fit else None
  rows.append(dict(index=i,known=enc((a,b)),rx=enc((c,d)),correlation=enc(corr[i]),known_energy=str(a*a+b*b),rx_energy=str(c*c+d*d),fit=enc(fit) if fit else None,residual=enc(res) if res else None,residual_energy=str(res[0]*res[0]+res[1]*res[1]) if res else None))
 minimum=F(inp['min_gain_sq']);maximum=F(inp['max_residual']);mp=h2>=minimum if h2 is not None else None;rp=nr<=maximum if nr is not None else None
 hard=['NO_PILOT_ENERGY'] if ek==0 else ['ZERO_GAIN'] if h2==0 else []
 policies={}
 for name in ['gated','naive']:
  reasons=hard[:] if hard else ([q for flag,q in [(mp,'LOW_MAGNITUDE'),(rp,'HIGH_RESIDUAL')] if not flag] if name=='gated' else [])
  corrected=None;decisions=None;factor=None
  if not reasons:
   a,b=h;factor=[str(a/h2),str(-b/h2)];corrected=[[str((c*a+d*b)/h2),str((d*a-c*b)/h2)] for c,d in x];decisions=[int(F(z[0])<0) for z in corrected]
  policies[name]=dict(status='REFUSED' if reasons else 'ACCEPTED',reasons=reasons,factor=factor,corrected=corrected,decisions=decisions,demodulated=not bool(reasons))
 return dict(status='OBSERVED',input=inp,stats=dict(known_energy=str(ek),rx_energy=str(er),numerator=enc(num),h=enc(h) if h else None,h2=str(h2) if h2 is not None else None,sse=str(sse) if sse is not None else None,normalized_residual=str(nr) if nr is not None else None),rows=rows,gates=dict(min_gain_sq=inp['min_gain_sq'],max_residual=inp['max_residual'],magnitude_pass=mp,residual_pass=rp),policies=policies)

def compare(out,truth):
 result={}
 for name,p in out.get('policies',{}).items():
  bits=p['decisions'];errs=[i for i,(a,b) in enumerate(zip(bits,truth)) if a!=b] if bits is not None else None;n=len(bits) if bits is not None else 0
  result[name]=dict(compared_bits=n,error_positions=errs,error_count=len(errs) if errs is not None else None,ber=str(F(len(errs),n)) if n else None,verdict='REFUSED' if bits is None else 'ACCEPTED_ERROR' if errs else 'ACCEPTED_CORRECT')
 return dict(truth=truth,policies=result,successful_receptions=sum(x['verdict']=='ACCEPTED_CORRECT' for x in result.values()))

def check(out,inp,literal=None,truth=None):
 if literal and literal.get('failure'):assert out==dict(status='EXECUTION_FAILED',reason='INJECTED_RUNTIME_ERROR');return
 assert out==expected(inp),'independent arithmetic differs'
 if literal:
  st=out['stats'];assert [st[k] for k in ['h','h2','known_energy','rx_energy','sse','normalized_residual']]==[literal[k] for k in ['h','h2','ek','er','sse','nr']],'hand metric'
  assert out['policies']['gated']['reasons']==literal['reasons'],'hand gate'
  audit=compare(out,truth);assert [x['error_count'] for x in audit['policies'].values()]==literal['errors'],'hand payload'
 if truth is not None:
  audit=compare(out,truth)
  for name,p in out['policies'].items():
   if p['status']=='REFUSED':assert p['decisions'] is None and p['corrected'] is None and not p['demodulated'];assert audit['policies'][name]['ber'] is None and audit['policies'][name]['compared_bits']==0
if __name__=='__main__':
 try:
  x=json.load(sys.stdin);check(x['result'],x['input']);print(json.dumps(dict(status='AUDIT_PASSED')))
 except Exception as e:print(json.dumps(dict(status='AUDIT_FAILED',reason=str(e))));sys.exit(1)

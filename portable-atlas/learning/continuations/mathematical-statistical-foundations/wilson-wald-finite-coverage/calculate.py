"""Decimal endpoint formula and nine binomial terms; no literal oracle import."""
import datetime,json,math,sys
from decimal import Decimal as D,localcontext
sys.dont_write_bytecode=True
class Refusal(ValueError):pass
def pairs(xs):
 d={}
 for k,v in xs:
  if k in d:raise Refusal('json_syntax')
  d[k]=v
 return d
def reject_constant(_):raise Refusal('json_syntax')
def calculate(text):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  try:x=json.loads(text,object_pairs_hook=pairs,parse_constant=reject_constant)
  except (json.JSONDecodeError,Refusal):raise Refusal('json_syntax')
  if type(x) is not dict or set(x)!={'n','p','z','k'}:raise Refusal('shape')
  if type(x['n']) is not int or x['n']!=8:raise Refusal('n')
  if type(x['p']) is not str or x['p'] not in ['0.1','0.5','0.9']:raise Refusal('p')
  if type(x['z']) is not str or x['z']!='1.96':raise Refusal('z')
  if type(x['k']) is not int or not 0<=x['k']<=8:raise Refusal('k')
 except Refusal as e:return {'status':'input_refusal','code':str(e),'summary':None,'rows':None},2
 with localcontext() as ctx:
  ctx.prec=40;ctx.rounding='ROUND_HALF_EVEN';p=D(x['p']);z=D(x['z']);n=D(8);rows=[];coverage={'wald':D(0),'wilson':D(0)};covered={'wald':[],'wilson':[]}
  for k in range(9):
   a=D(k)/n;v=a*(1-a)/n;wh=z*v.sqrt();wl=a-wh;wu=a+wh
   den=1+z*z/n;center=(a+z*z/(2*n))/den;half=z*(v+z*z/(4*n*n)).sqrt()/den
   sl=center-half;su=center+half
   if k==0:sl=D(0);su=z*z/(n+z*z)
   if k==8:sl=n/(n+z*z);su=D(1)
   mass=D(math.comb(8,k))*p**k*(1-p)**(8-k);methods={}
   for name,l,u in [('wald',wl,wu),('wilson',sl,su)]:
    contains=l<=p<=u
    methods[name]={'lower':str(l),'upper':str(u),'width':str(u-l),'contains':contains,'outside_0_1':l<0 or u>1}
    if contains:covered[name].append(k);coverage[name]+=mass
   rows.append({'k':k,'estimate':str(a),'mass':str(mass),**methods})
  summary={'input':x,'category':'equal' if coverage['wilson']==coverage['wald'] else 'wilson' if coverage['wilson']>coverage['wald'] else 'wald','coverage':{m:str(c) for m,c in coverage.items()},'covered_k':covered,'delta':str(coverage['wilson']-coverage['wald']),'nominal':'0.95','difference_from_nominal':{m:str(c-D('.95')) for m,c in coverage.items()},'selected':rows[x['k']],'probability_sum':str(sum(D(r['mass']) for r in rows))}
 return {'status':'calculated','summary':summary,'rows':rows,'context':{'n':8,'precision':40,'rounding':'ROUND_HALF_EVEN','z':'rounded 1.96','wald_clipping':False,'wilson_boundary':'analytic k0/k8, no clipping','sample_space':'all 256 independent Bernoulli sequences, aggregated nine binomial terms','true_p':'known only for educational coverage calculation; not real-data inference'},'started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},0
if __name__=='__main__':
 try:r,code=calculate(sys.stdin.read())
 except Exception as e:r={'status':'execution_error','summary':None,'rows':None,'error_class':type(e).__name__};code=3
 print(json.dumps(r,ensure_ascii=False));sys.exit(code)

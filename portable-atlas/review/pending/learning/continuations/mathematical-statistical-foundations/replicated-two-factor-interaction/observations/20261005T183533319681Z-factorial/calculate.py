"""Exact cell-mean contrasts on finite synthetic integer replicates."""
import datetime,json,sys
from fractions import Fraction as F
sys.dont_write_bytecode=True
class Refusal(ValueError):pass
def pairs(xs):
 d={}
 for k,v in xs:
  if k in d:raise Refusal('json_syntax')
  d[k]=v
 return d
def constant(_):raise Refusal('json_syntax')
def calculate(text):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  try:x=json.loads(text,object_pairs_hook=pairs,parse_constant=constant)
  except (json.JSONDecodeError,Refusal):raise Refusal('json_syntax')
  if type(x) is not dict or set(x)!={'unit','cells'}:raise Refusal('shape')
  if x['unit']!='arb' or type(x['unit']) is not str:raise Refusal('unit')
  if type(x['cells']) is not list or len(x['cells'])!=4:raise Refusal('cells')
  if any(type(c) is not list or len(c)!=3 for c in x['cells']):raise Refusal('replicates')
  if any(type(v) is not int or not -20<=v<=40 for c in x['cells'] for v in c):raise Refusal('values')
 except Refusal as e:return {'status':'input_refusal','code':str(e),'summary':None,'cells':None},2
 means=[sum(map(F,c))/3 for c in x['cells']];m00,m10,m01,m11=means;grand=sum(means)/4
 contrasts={'A':(-m00+m10-m01+m11)/2,'B':(-m00-m10+m01+m11)/2,'AB':(m00-m10-m01+m11)/2};beta={'I':grand,**{name:v/2 for name,v in contrasts.items()}};slope0=m10-m00;slope1=m11-m01;dod=slope1-slope0
 cells=[];within=F(0)
 for i,(raw,m) in enumerate(zip(x['cells'],means)):
  sse=sum((F(v)-m)**2 for v in raw);within+=sse;cells.append({'id':['A-B-','A+B-','A-B+','A+B+'][i],'levels':[[-1,-1],[1,-1],[-1,1],[1,1]][i],'observations':raw,'mean':str(m),'SSE':str(sse),'sample_variance':str(sse/2)})
 ss={name:12*b*b for name,b in beta.items() if name!='I'};ss['within']=within;ss['total']=sum((F(v)-grand)**2 for c in x['cells'] for v in c)
 additive=[grand+beta['A']*a+beta['B']*b for a,b in [(-1,-1),(1,-1),(-1,1),(1,1)]];ofatpred=m10+m01-m00
 summary={'input':x,'category':'crossover' if slope0*slope1<0 else 'interaction' if dod else 'additive','N':12,'r':3,'means':[str(v) for v in means],'effects':{n:str(v) for n,v in contrasts.items()},'coefficients':{n:str(v) for n,v in beta.items()},'conditional_A':{'B-':str(slope0),'B+':str(slope1)},'DOD':str(dod),'SS':{n:str(v) for n,v in ss.items()},'df':{'A':1,'B':1,'AB':1,'within':8,'total':11},'MSE':str(within/8),'main_only_fitted_means':[str(v) for v in additive],'main_only_SSE':str(within+ss['AB']),'ofat':{'observed_cells':[0,1,2],'missing_cell':3,'missing_prediction':str(ofatpred),'actual_missing_mean':str(m11),'prediction_error':str(m11-ofatpred),'interaction_identifiable':False},'units':{'response':'arb','effects':'arb','coefficients':'arb','SS':'arb^2','MSE':'arb^2'}}
 return {'status':'calculated','summary':summary,'cells':cells,'context':{'synthetic':True,'physical_replication_performed':False,'randomized_execution':False,'temporal_run_order_observed':False,'design_display_order':['A-B-','A+B-','A-B+','A+B+'],'coding':[-1,1],'model':'y=I+A*xA+B*xB+AB*xA*xB','effect_equals':'2*coefficient','DOD_equals':'4*coefficientAB','significance_test_performed':False,'causal_claim':False,'OFAT':'projection of first three synthetic cells; fourth mean predicted under no-interaction assumption, not measured in OFAT'},'started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},0
if __name__=='__main__':
 try:r,exitcode=calculate(sys.stdin.read())
 except Exception as e:r={'status':'execution_error','summary':None,'cells':None,'error_class':type(e).__name__};exitcode=3
 print(json.dumps(r,ensure_ascii=False));sys.exit(exitcode)

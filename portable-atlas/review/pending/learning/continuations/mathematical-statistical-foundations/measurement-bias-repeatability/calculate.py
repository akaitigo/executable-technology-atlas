import datetime,json,sys
from fractions import Fraction as F
sys.dont_write_bytecode=True
class Refusal(Exception):pass
def reject(code):raise Refusal(code)
def pairs(items):
 d={}
 for k,v in items:
  if k in d:reject('json_syntax')
  d[k]=v
 return d
def parse(text):
 try:x=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda _:reject('json_syntax'))
 except (ValueError,TypeError):reject('json_syntax')
 if not isinstance(x,dict) or set(x)!=set(['unit','references','operators','cells']):reject('shape')
 if x['unit']!='arb':reject('unit')
 if x['references']!=[10,20] or any(type(v) is not int for v in x['references']):reject('references')
 if x['operators']!=['A','B']:reject('operators')
 a=x['cells']
 if not isinstance(a,list) or len(a)!=4:reject('cells')
 for row in a:
  if not isinstance(row,list) or len(row)!=3:reject('replicates')
  if any(type(v) is not int or not -20<=v<=50 for v in row):reject('values')
 return x
def compute(x):
 cells=[]
 for i,values in enumerate(x['cells']):
  ref=x['references'][i//2];mean=sum(map(F,values))/3;bias=mean-ref;sse=sum((F(v)-mean)**2 for v in values);s2=sse/2;mse=sum((F(v)-ref)**2 for v in values)/3
  cells.append({'id':str(ref)+x['operators'][i%2],'reference':ref,'operator':x['operators'][i%2],'observations':values,'mean':str(mean),'bias':str(bias),'SSE':str(sse),'sample_variance':str(s2),'df':2,'population_variance':str(sse/3),'reference_MSE':str(mse),'bias_flag':abs(bias)>1,'spread_flag':s2>2})
 values=sum(x['cells'],[]);grand=sum(map(F,values))/12;within=sum(F(c['SSE']) for c in cells);between=3*sum((F(c['mean'])-grand)**2 for c in cells);total=sum((F(v)-grand)**2 for v in values);bias=sum(F(c['bias']) for c in cells)/4;biasflags=[c['id'] for c in cells if c['bias_flag']];spreadflags=[c['id'] for c in cells if c['spread_flag']]
 category='both' if biasflags and spreadflags else 'bias' if biasflags else 'spread' if spreadflags else 'within'
 return {'input':x,'category':category,'cells':cells,'within_SSE':str(within),'within_df':8,'within_sample_variance':str(within/8),'naive_all_values_sample_variance':str(total/11),'all_values_SSE':str(total),'between_cell_SSE':str(between),'grand_mean':str(grand),'aggregate_signed_bias':str(bias),'max_abs_cell_bias':str(max(abs(F(c['bias'])) for c in cells)),'fixed_operator_differences':[str(F(cells[i+1]['mean'])-F(cells[i]['mean'])) for i in [0,2]],'bias_flags':biasflags,'spread_flags':spreadflags,'bias_limit':'1','sample_variance_limit':'2','rule':'abs(cell bias)>1 and cell sample_variance>2 separately; equality inside','units':{'response_reference_mean_bias':'arb','SSE_variance_MSE':'arb^2'},'pooling':'finite descriptive within SS/df8; no equal-precision validation'}
def main():
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  x=parse(sys.stdin.read());s=compute(x);r={'status':'calculated','summary':s,'context':{'synthetic':True,'references_assumed_constants':True,'reference_truth_guaranteed':False,'physical_instrument_measured':False,'calibration_traceability_established':False,'uncertainty_budget_implemented':False,'statistical_independence_established':False,'randomization_executed':False,'equal_precision_established':False,'full_gage_RR_components_implemented':False,'population_operator_reproducibility_estimated':False,'product_process_variation_estimated':False,'cause_identified':False,'significance_test_implemented':False},'started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};code=0
 except Refusal as e:r={'status':'input_refusal','code':str(e),'summary':None};code=2
 except Exception as e:r={'status':'execution_error','error_class':type(e).__name__,'summary':None};code=3
 print(json.dumps(r,ensure_ascii=False));return code
if __name__=='__main__':sys.exit(main())

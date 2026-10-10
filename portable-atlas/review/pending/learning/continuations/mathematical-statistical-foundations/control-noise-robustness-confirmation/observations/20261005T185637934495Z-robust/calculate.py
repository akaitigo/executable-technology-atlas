import datetime,json,re,sys
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
def metrics(fixture,target):
 result={};cells=[]
 for c in range(2):
  raw=fixture['cells'][2*c:2*c+2];flat=[F(v) for cell in raw for v in cell];mean=sum(flat)/6;ss=sum((v-mean)**2 for v in flat);means=[];within=F(0)
  for n,values in enumerate(raw):
   m=sum(map(F,values))/3;err=sum((F(v)-m)**2 for v in values);means.append(m);within+=err/6;cells.append({'control':'C'+str(c),'noise':[-1,1][n],'observations':values,'mean':str(m),'SSE':str(err),'sample_variance':str(err/2)})
  result['C'+str(c)]={'mean':str(mean),'bias':str(mean-target),'variance_N':str(ss/6),'sample_variance_Nminus1':str(ss/5),'within_population_component':str(within),'between_noise_component':str(sum((m-mean)**2 for m in means)/2),'noise_difference':str(means[1]-means[0]),'loss':str(sum((v-target)**2 for v in flat)/6),'N':6,'sample_df':5}
 return {'fixture_id':fixture['id'],'settings':result,'cells':cells}
def calculate(text):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  try:x=json.loads(text,object_pairs_hook=pairs,parse_constant=constant)
  except (json.JSONDecodeError,Refusal):raise Refusal('json_syntax')
  if type(x) is not dict or set(x)!={'unit','target','loss_limit','selection','confirmation'}:raise Refusal('shape')
  if type(x['unit']) is not str or x['unit']!='arb':raise Refusal('unit')
  if type(x['target']) is not int or x['target']!=10:raise Refusal('target')
  if type(x['loss_limit']) is not int or x['loss_limit']!=3:raise Refusal('loss_limit')
  for key in ['selection','confirmation']:
   f=x[key]
   if type(f) is not dict or set(f)!={'id','cells'}:raise Refusal('fixture-shape')
   if type(f['id']) is not str or not re.fullmatch('[a-z][a-z0-9-]{0,31}',f['id']):raise Refusal('fixture-id')
   if type(f['cells']) is not list or len(f['cells'])!=4:raise Refusal('cells')
   if any(type(c) is not list or len(c)!=3 for c in f['cells']):raise Refusal('replicates')
   if any(type(v) is not int or not -20<=v<=40 for c in f['cells'] for v in c):raise Refusal('values')
  if x['selection']['id']==x['confirmation']['id']:raise Refusal('fixture-id')
  if x['selection']['cells']==x['confirmation']['cells']:raise Refusal('fixture-reuse')
 except Refusal as e:return {'status':'input_refusal','code':str(e),'summary':None},2
 select=metrics(x['selection'],F(x['target']));minimum=min(F(v['loss']) for v in select['settings'].values());winners=[c for c,m in select['settings'].items() if F(m['loss'])==minimum];winner=winners[0] if len(winners)==1 else None;confirm=None
 if winner is not None:
  confirm=metrics(x['confirmation'],F(x['target']));heldloss=F(confirm['settings'][winner]['loss']);category='pass' if heldloss<=x['loss_limit'] else 'fail';sequence=['selection-evaluated','setting-locked','confirmation-evaluated']
 else:heldloss=None;category='tie';sequence=['selection-evaluated','no-unique-choice'];
 summary={'input':x,'category':category,'selection':select,'winner':winner,'selection_candidates':winners,'selection_loss':str(minimum),'confirmation':confirm,'confirmation_loss':None if heldloss is None else str(heldloss),'loss_limit':'3','confirmation_executed':winner is not None,'sequence':sequence,'winner_reselected_on_confirmation':False,'units':{'response':'arb','mean_bias_noise_difference':'arb','variance_loss':'arb^2'},'noise_weights':['1/2','1/2'],'loss_definition':'mean((y-10)^2) = bias^2 + variance_N, not sample_variance_Nminus1'}
 return {'status':'calculated','summary':summary,'context':{'synthetic':True,'different_fixture_ids_and_arrays':True,'statistical_independence_established':False,'physical_noise_trial':False,'physical_replication':False,'randomized_execution':False,'signal_factor_varied':False,'control':'setting C0/C1 selectable in model','noise':'two imposed synthetic N-/N+ conditions, equal weight, not real use distribution','parameter_design':'finite setting selection only','tolerance_design':False,'SN_ratio_implemented':False,'orthogonal_array_implemented':False,'causality_or_significance_test':False},'started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},0
if __name__=='__main__':
 try:r,code=calculate(sys.stdin.read())
 except Exception as e:r={'status':'execution_error','summary':None,'error_class':type(e).__name__};code=3
 print(json.dumps(r,ensure_ascii=False));sys.exit(code)

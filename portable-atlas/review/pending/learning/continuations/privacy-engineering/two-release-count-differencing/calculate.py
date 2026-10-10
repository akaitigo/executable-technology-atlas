import datetime,itertools,json,sys
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
 if not isinstance(x,dict) or set(x)!=set(['categories','before','after','target_added','background']):reject('shape')
 if x['categories']!=['A','B','C']:reject('categories')
 for name in ['before','after']:
  a=x[name]
  if not isinstance(a,list) or len(a)!=3 or any(type(v) is not int or not 0<=v<=6 for v in a):reject('counts')
 if x['target_added'] is not True:reject('target-premise')
 b=x['background']
 if not isinstance(b,dict) or set(b)!=set(['max_add','max_delete']) or any(type(v) is not int or not 0<=v<=2 for v in b.values()):reject('background')
 return x
def vectors(bound):return [list(v) for v in itertools.product(range(bound+1),repeat=3) if sum(v)<=bound]
def compute(x):
 adds=vectors(x['background']['max_add']);deletes=[d for d in vectors(x['background']['max_delete']) if all(d[i]<=x['before'][i] for i in range(3))];witnesses=[]
 for t,label in enumerate(x['categories']):
  for a in adds:
   for d in deletes:
    after=[x['before'][i]+int(i==t)+a[i]-d[i] for i in range(3)]
    if after==x['after']:witnesses.append({'target':label,'add':a,'delete':d})
 candidates=[c for c in x['categories'] if any(w['target']==c for w in witnesses)];delta=[x['after'][i]-x['before'][i] for i in range(3)];naive=next((x['categories'][i] for i in range(3) if delta==[int(j==i) for j in range(3)]),None);category='known' if len(candidates)==1 else 'ambiguous' if candidates else 'inconsistent'
 return {'input':x,'delta':delta,'category':category,'candidates':candidates,'known_category':candidates[0] if len(candidates)==1 else None,'witnesses':witnesses,'witness_count':len(witnesses),'candidate_witness_counts':{c:sum(w['target']==c for w in witnesses) for c in x['categories']},'enumerated_transition_count':3*len(adds)*len(deletes),'maximum_transition_count':300,'naive_category_ignoring_background':naive,'naive_uniqueness_justified':naive is not None and candidates==[naive],'target_presence':'given added once and still present; not inferred from counts','delete_capacity_rule':'background delete <= before; no target/new record deletion','candidate_semantics':'count-vector witnesses only; not individual linkage or probability','equation':'after = before + unit(target) + background_add - baseline_delete','units':'synthetic record counts'}
def main():
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  x=parse(sys.stdin.read());r={'status':'calculated','summary':compute(x),'context':{'synthetic_only':True,'target_addition_given':True,'target_presence_inferred':False,'actual_person_linked':False,'external_dataset_used':False,'real_reidentification_rate_estimated':False,'DP_guarantee_implemented':False,'law_compliance_assessed':False,'publication_performed':False,'count_witnesses_have_probabilities':False,'background_record_identity_determined':False},'started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};code=0
 except Refusal as e:r={'status':'input_refusal','code':str(e),'summary':None};code=2
 except Exception as e:r={'status':'execution_error','error_class':type(e).__name__,'summary':None};code=3
 print(json.dumps(r,ensure_ascii=False));return code
if __name__=='__main__':sys.exit(main())

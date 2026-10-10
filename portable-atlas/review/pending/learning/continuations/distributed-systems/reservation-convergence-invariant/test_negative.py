import json,sys,copy,subprocess
from pathlib import Path
from oracle import check
P=Path(__file__).resolve().parent
base=json.loads((P/'fixture.json').read_text())[0]['input']
def produce(x):
 r=subprocess.run([sys.executable,'-B','model.py'],input=json.dumps(x),text=True,capture_output=True,cwd=P);assert r.returncode==0;return json.loads(r.stdout)
def collect():
 original=produce(base);mutants=[]
 def mutate(label,fn):
  r=copy.deepcopy(original);fn(r)
  try:check(r,base);detected=False
  except AssertionError:detected=True
  mutants.append(dict(id=label,detected=detected))
 mutate('convergence-is-safety',lambda r:r['policies']['optimistic']['final'].__setitem__('global_business_ok',True))
 mutate('remove-accepted-after-union',lambda r:r['policies']['optimistic']['final'].__setitem__('accepted_returned',['a']))
 mutate('prune-local-to-stock',lambda r:r['policies']['optimistic']['final']['local_sets'].__setitem__('B',['a']))
 mutate('overwrite-not-union',lambda r:r['policies']['optimistic']['trace'][-1]['local_sets'].__setitem__('A',['b']))
 mutate('pending-rounded-success',lambda r:r['policies']['deferred']['trace'][2]['latest_responses'].__setitem__('b','accepted'))
 mutate('pending-rounded-rejected',lambda r:r['policies']['deferred']['trace'][2]['latest_responses'].__setitem__('b','rejected'))
 mutate('recover-delivers',lambda r:r['policies']['optimistic']['trace'][3]['local_sets'].__setitem__('A',['a','b']))
 mutate('reverse-serial-winner',lambda r:r['policies']['deferred']['final'].__setitem__('accepted_returned',['b']))
 mutate('erased-response-history',lambda r:r['policies']['optimistic']['final'].__setitem__('response_history',[]))
 mutate('lost-pending-phase',lambda r:r['policies']['deferred']['final']['response_history'].pop(0))
 mutate('invented-delivery-complete',lambda r:r['policies']['deferred'].__setitem__('all_messages_delivered',False))
 mutate('wrong-local-decision',lambda r:r['policies']['optimistic']['trace'][1]['local_decision'].__setitem__('status','pending'))
 mutate('wrong-response-event',lambda r:r['policies']['deferred']['trace'][4]['response_event'].__setitem__('status','rejected'))
 mutate('message-snapshot-relabel',lambda r:r['policies']['optimistic']['final']['messages'].__setitem__('A>B',['b']))
 mutate('link-up-during-partition',lambda r:r['policies']['optimistic']['trace'][2].__setitem__('link_up',True))
 mutate('wrong-replica-bound',lambda r:r['policies']['optimistic']['final']['replica_bounds'].__setitem__('A',True))
 mutate('empty-delivered-set',lambda r:r['policies']['optimistic']['final']['delivered_set'].__setitem__('A',[]))
 mutate('duplicate-count',lambda r:r['policies']['optimistic']['final']['delivery_count'].__setitem__('B',2))
 mutate('false-converged',lambda r:r['policies']['optimistic']['trace'][2].__setitem__('converged',True))
 mutate('snapshot-altered-after-send',lambda r:r['policies']['deferred']['trace'][7]['messages'].__setitem__('B>A',['a']))
 mutate('input-capacity-rewritten',lambda r:r['input_echo'].__setitem__('capacity',2))
 bad=[]
 def invalid(id,fn):
  x=copy.deepcopy(base);fn(x);bad.append((id,json.dumps(x)))
 invalid('bool-capacity',lambda x:x.__setitem__('capacity',True))
 invalid('negative-capacity',lambda x:x.__setitem__('capacity',-1))
 invalid('capacity-four',lambda x:x.__setitem__('capacity',4))
 invalid('duplicate-request-id',lambda x:x['requests'][1].__setitem__('id','a'))
 invalid('unknown-replica',lambda x:x['requests'][1].__setitem__('replica','C'))
 invalid('missing-serial',lambda x:x.__setitem__('serial_order',['a']))
 invalid('duplicate-serial',lambda x:x.__setitem__('serial_order',['a','a']))
 invalid('unknown-delivery',lambda x:x.__setitem__('schedule',['C>A']))
 invalid('too-long-schedule',lambda x:x.__setitem__('schedule',['A>B']*7))
 invalid('extra-field',lambda x:x.__setitem__('accepted',True))
 invalid('integer-id',lambda x:x['requests'][0].__setitem__('id',1))
 bad.append(('malformed-json','{'))
 refused=[]
 for label,text in bad:
  r=subprocess.run([sys.executable,'-B','model.py'],input=text,text=True,capture_output=True,cwd=P);out=json.loads(r.stdout);refused.append(dict(id=label,exit=r.returncode,result=out,detected=r.returncode==2 and out['status']=='INPUT_REFUSED'))
 return dict(status='passed' if all(m['detected'] for m in mutants+refused) else 'failed',mutants=mutants,refusals=refused)
if __name__=='__main__':
 r=collect()
 if sys.argv[1:]==['--record']:(P/'evidence/negative.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r));sys.exit(r['status']!='passed')

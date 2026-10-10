import pathlib,json,hashlib,sqlite3
R=pathlib.Path(__file__).resolve().parent
EXPECTED={'poison-only': {'inbox': [], 'effects': [], 'account': [[1, 0]], 'attempts': [[1, 0, 0, 1, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [2, 1, 0, 2, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [3, 3, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None]], 'dlq': [[1, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'poison-exhausted', '[1,2,3]', None]], 'redrive': []}, 'poison-corrected': {'inbox': [['m1', '{"delta":7,"id":"m1"}']], 'effects': [[1, 'm1', 7, '{"delta":7,"id":"m1"}', 4, 1]], 'account': [[1, 7]], 'attempts': [[1, 0, 0, 1, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [2, 1, 0, 2, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [3, 3, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [4, 4, 1, 1, 'm1', '{"delta":7,"id":"m1"}', 'COMMITTED', 0, 1]], 'dlq': [[1, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'poison-exhausted', '[1,2,3]', None]], 'redrive': [[1, 1, 1, 4, '{"delta":7,"id":"m1"}', '[4]', None, 'COMMITTED']]}, 'poison-unchanged': {'inbox': [], 'effects': [], 'account': [[1, 0]], 'attempts': [[1, 0, 0, 1, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [2, 1, 0, 2, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [3, 3, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [4, 4, 1, 1, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, 1], [5, 5, 1, 2, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, 1], [6, 7, 1, 3, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, 1]], 'dlq': [[1, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'poison-exhausted', '[1,2,3]', None], [2, 1, 7, 'm1', '{"delta":"poison","id":"m1"}', 'poison-exhausted', '[4,5,6]', 1]], 'redrive': [[1, 1, 1, 4, '{"delta":"poison","id":"m1"}', '[4,5,6]', 2, 'POISON_EXHAUSTED']]}, 'committed-same': {'inbox': [['m1', '{"delta":7,"id":"m1"}']], 'effects': [[1, 'm1', 7, '{"delta":7,"id":"m1"}', -1, -1]], 'account': [[1, 7]], 'attempts': [[1, -1, -1, 1, 'm1', '{"delta":7,"id":"m1"}', 'COMMITTED', 0, None], [2, 0, 0, 1, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [3, 1, 0, 2, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [4, 3, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [5, 4, 1, 1, 'm1', '{"delta":7,"id":"m1"}', 'DUPLICATE', 0, 1]], 'dlq': [[1, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'poison-exhausted', '[2,3,4]', None]], 'redrive': [[1, 1, 1, 4, '{"delta":7,"id":"m1"}', '[5]', None, 'DUPLICATE']]}, 'committed-changed': {'inbox': [['m1', '{"delta":7,"id":"m1"}']], 'effects': [[1, 'm1', 7, '{"delta":7,"id":"m1"}', -1, -1]], 'account': [[1, 7]], 'attempts': [[1, -1, -1, 1, 'm1', '{"delta":7,"id":"m1"}', 'COMMITTED', 0, None], [2, 0, 0, 1, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [3, 1, 0, 2, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [4, 3, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [5, 4, 1, 1, 'm1', '{"delta":9,"id":"m1"}', 'CONFLICT', 66, 1]], 'dlq': [[1, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'poison-exhausted', '[2,3,4]', None], [2, 1, 4, 'm1', '{"delta":9,"id":"m1"}', 'identity-conflict', '[5]', 1]], 'redrive': [[1, 1, 1, 4, '{"delta":9,"id":"m1"}', '[5]', 2, 'CONFLICT']]}, 'committed-changed-id-only': {'inbox': [['m1', '{"delta":7,"id":"m1"}']], 'effects': [[1, 'm1', 7, '{"delta":7,"id":"m1"}', -1, -1]], 'account': [[1, 7]], 'attempts': [[1, -1, -1, 1, 'm1', '{"delta":7,"id":"m1"}', 'COMMITTED', 0, None], [2, 0, 0, 1, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [3, 1, 0, 2, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [4, 3, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'POISON', 65, None], [5, 4, 1, 1, 'm1', '{"delta":9,"id":"m1"}', 'DUPLICATE_ID_ONLY', 0, 1]], 'dlq': [[1, 0, 3, 'm1', '{"delta":"poison","id":"m1"}', 'poison-exhausted', '[2,3,4]', None]], 'redrive': [[1, 1, 1, 4, '{"delta":9,"id":"m1"}', '[5]', None, 'DUPLICATE_ID_ONLY']]}}
SPECS={'poison-only': {'seed': False, 'redrive': None, 'ticks': [], 'outcomes': [], 'terminal': 'NONE', 'effectTick': None, 'balance': 0}, 'poison-corrected': {'seed': False, 'redrive': '{"delta":7,"id":"m1"}', 'ticks': [4], 'outcomes': ['COMMITTED'], 'terminal': 'COMMITTED', 'effectTick': 4, 'balance': 7}, 'poison-unchanged': {'seed': False, 'redrive': '{"delta":"poison","id":"m1"}', 'ticks': [4, 5, 7], 'outcomes': ['POISON', 'POISON', 'POISON'], 'terminal': 'POISON_EXHAUSTED', 'effectTick': None, 'balance': 0}, 'committed-same': {'seed': True, 'redrive': '{"delta":7,"id":"m1"}', 'ticks': [4], 'outcomes': ['DUPLICATE'], 'terminal': 'DUPLICATE', 'effectTick': -1, 'balance': 7}, 'committed-changed': {'seed': True, 'redrive': '{"delta":9,"id":"m1"}', 'ticks': [4], 'outcomes': ['CONFLICT'], 'terminal': 'CONFLICT', 'effectTick': -1, 'balance': 7}, 'committed-changed-id-only': {'seed': True, 'redrive': '{"delta":9,"id":"m1"}', 'ticks': [4], 'outcomes': ['DUPLICATE_ID_ONLY'], 'terminal': 'DUPLICATE_ID_ONLY', 'effectTick': -1, 'balance': 7}}
CONTRACT={'originalId': 'm1', 'originalPayload': '{"delta":"poison","id":"m1"}', 'originalAttemptTicks': [0, 1, 3], 'seedCommitTick': -1, 'redriveTicks': [4, 5, 7], 'attemptLimit': 3, 'validationBeforeInbox': True, 'inboxIdentity': 'canonical full JSON id+delta, strict mode compares payload; id-only intentionally omits comparison', 'transaction': 'inbox/effect/account same SQLite transaction; driver ack and DLQ are model', 'history': 'append-only DLQ rows; redrive source_dlq links new generation/attempts; conflict stops immediately', 'finite': 'one original + at most one redrive; no sleep, broker, external effect or durability claim'}
REQUESTS={'poison-only': {'seed': False, 'mode': 'strict', 'redrive': None}, 'poison-corrected': {'seed': False, 'mode': 'strict', 'redrive': {'id': 'm1', 'delta': 7}}, 'poison-unchanged': {'seed': False, 'mode': 'strict', 'redrive': {'id': 'm1', 'delta': 'poison'}}, 'committed-same': {'seed': True, 'mode': 'strict', 'redrive': {'id': 'm1', 'delta': 7}}, 'committed-changed': {'seed': True, 'mode': 'strict', 'redrive': {'id': 'm1', 'delta': 9}}, 'committed-changed-id-only': {'seed': True, 'mode': 'id-only', 'redrive': {'id': 'm1', 'delta': 9}}, 'refused-new-id': {'seed': False, 'mode': 'strict', 'redrive': {'id': 'm2', 'delta': 7}}, 'refused-mode': {'seed': False, 'mode': True, 'redrive': None}, 'execution-failure': {'rawInput': '{"seed":'}}

QUERIES={'inbox':'SELECT id,payload FROM inbox ORDER BY id','effects':'SELECT effect_no,message_id,delta,payload,tick,generation FROM effects ORDER BY effect_no','account':'SELECT singleton,balance FROM account','attempts':'SELECT attempt_id,tick,generation,ordinal,message_id,payload,outcome,exit_code,source_dlq FROM attempts ORDER BY attempt_id','dlq':'SELECT dlq_id,generation,tick,message_id,payload,reason,attempt_ids,source_dlq FROM dlq ORDER BY dlq_id','redrive':'SELECT redrive_id,source_dlq,generation,start_tick,payload,attempt_ids,terminal_dlq,terminal_outcome FROM redrive ORDER BY redrive_id'}
def sha(b):return hashlib.sha256(b).hexdigest()
def rows(path):
 db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
 try:
  db.execute('PRAGMA query_only=ON')
  assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  return {name:[list(row) for row in db.execute(sql)] for name,sql in QUERIES.items()}
 finally:db.close()
def check(root=R):
 run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text())
 assert (run/'stdout.json').read_bytes()==(run/'result.json').read_bytes()
 assert json.loads((root/'requests.json').read_text())==REQUESTS
 assert json.loads((root/'oracle.json').read_text())=={'contract':CONTRACT,'specs':SPECS,'tables':EXPECTED,'refusals':{'refused-new-id':'same-ID redrive required','refused-mode':'invalid mode'}}
 for n,h in d['sourceHashes'].items():assert sha((root/n).read_bytes())==h
 for n,v in json.loads((run/'artifacts.json').read_text())['files'].items():
  b=(run/n).read_bytes();assert sha(b)==v['sha256'] and len(b)==v['bytes'],n
 assert [c['id'] for c in d['cases']]==list(REQUESTS)
 for c in d['cases']:
  name=c['id'];folder=run/name;x=REQUESTS[name]
  inp=x['rawInput'].encode() if 'rawInput' in x else (json.dumps(x,sort_keys=True)+'\n').encode()
  assert (folder/'input.txt').read_bytes()==inp and sha(inp)==c['inputSha256']
  assert (folder/'stdout.txt').read_text()==c['stdout'] and (folder/'stderr.txt').read_text()==c['stderr']
  if name=='execution-failure':
   assert c['exitCode']==3 and c['outcome']=='EXECUTION_FAILURE' and c['observation'] is None and c['stdout']=='' and c['stderr'].startswith('JSONDecodeError:') and c['db'] is None;continue
  o=json.loads(c['stdout']);assert o==c['observation'] and c['stderr']==''
  if name.startswith('refused-'):
   reason='same-ID redrive required' if name=='refused-new-id' else 'invalid mode'
   assert c['exitCode']==2 and c['outcome']=='REFUSED' and c['db'] is None and o=={'observed':False,'reason':reason,'summary':None,'final':None,'commands':[]};continue
  assert c['exitCode']==0 and c['outcome']=='OBSERVED' and o['observed'] and o['reason'] is None
  expected=EXPECTED[name];s=SPECS[name];actual=rows(run/c['db']);assert actual==expected,(name,actual,expected)
  assert o['final']==expected
  baselineEffects=1 if s['seed'] else 0;effectCount=0 if s['effectTick'] is None else 1
  summary={'effectCount':effectCount,'baselineEffects':baselineEffects,'addedEffects':effectCount-baselineEffects,'balance':s['balance'],'terminalRedrive':s['terminal'],'initialAttemptTicks':[0,1,3],'redriveAttemptTicks':s['ticks'],'originalDLQPreserved':True}
  assert o['summary']==summary
  originalIds=[2,3,4] if s['seed'] else [1,2,3]
  before={'inbox':[['m1','{"delta":7,"id":"m1"}']] if s['seed'] else [],'effects':[[1,'m1',7,'{"delta":7,"id":"m1"}',-1,-1]] if s['seed'] else [],'account':[[1,7 if s['seed'] else 0]],'attempts':expected['attempts'][:4 if s['seed'] else 3],'dlq':expected['dlq'][:1],'redrive':[]}
  assert o['beforeRedrive']==before and o['final']['dlq'][0]==before['dlq'][0]
  assert len(o['commands'])==len(expected['attempts'])
  for command,row in zip(o['commands'],expected['attempts']):
   aid,tick,gen,ordinal,msg,payload,status,code,source=row
   assert [command['attemptId'],command['tick'],command['generation'],command['ordinal'],command['sourceDLQ'],command['exitCode']]==[aid,tick,gen,ordinal,source,code]
   assert command['argv']==['python3','-B','../consumer.py','state.sqlite',x['mode'],str(tick),str(gen)]
   assert command['stdin']==payload+'\n' and command['stderr']==''
   leaf=folder/('attempt-'+str(aid))
   assert (leaf/'input.txt').read_text()==command['stdin'] and (leaf/'stdout.txt').read_text()==command['stdout'] and (leaf/'stderr.txt').read_text()==command['stderr']
   assert json.loads((leaf/'command.json').read_text())==command
   consumer=json.loads(command['stdout']);assert consumer==command['observation']
   balance=0 if not s['seed'] and gen==0 or s['effectTick'] is None else 7
   stored=None if status=='POISON' else '{"delta":7,"id":"m1"}'
   assert {k:consumer[k] for k in ['status','ackModel','payload','storedPayload','effectAdded','balance']}=={'status':status,'ackModel':code==0,'payload':payload,'storedPayload':stored,'effectAdded':1 if status=='COMMITTED' else 0,'balance':balance}
   sql=consumer['sql'];assert sql[0]=='BEGIN IMMEDIATE'
   if status=='COMMITTED':
    assert sql[-2]=='COMMIT' and any(v.startswith('INSERT INTO inbox') for v in sql) and any(v.startswith('INSERT INTO effects') for v in sql) and any(v.startswith('UPDATE account') for v in sql)
   else:assert 'ROLLBACK' in sql and not any(v.startswith(('INSERT','UPDATE','DELETE')) for v in sql)
 return len(d['cases'])
if __name__=='__main__':check();print('PASS 9 cases; independent literal ticks/DLQ history/inbox/effects/balance via read-only SQL; consumer not imported')

import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parent
TABLES={'baseline': [[0, 0, [], False, 'A', True, 'read', None, 0, True, True]], 'ack-a': [[1, 0, [1], False, 'A', True, 'ack-a', 1, None, None, None], [1, 0, [1], False, 'A', True, 'read', None, 1, True, True]], 'failover-before-delivery': [[1, 0, [1], False, 'A', True, 'ack-a', 1, None, None, None], [1, 0, [1], False, 'B', True, 'route', None, None, None, None], [1, 0, [1], False, 'B', True, 'read', None, 0, True, False]], 'delivered-before-failover': [[1, 0, [1], False, 'A', True, 'ack-a', 1, None, None, None], [1, 1, [], False, 'A', True, 'delivered', None, None, None, None], [1, 1, [], False, 'B', True, 'route', None, None, None, None], [1, 1, [], False, 'B', True, 'read', None, 1, True, True]], 'partition-read': [[1, 0, [1], False, 'A', True, 'ack-a', 1, None, None, None], [1, 0, [1], True, 'A', True, 'partition', None, None, None, None], [1, 0, [1], True, 'B', True, 'route', None, None, None, None], [1, 0, [1], True, 'B', True, 'delivery-blocked', None, None, None, None], [1, 0, [1], True, 'B', True, 'read', None, 0, True, False]], 'heal-deliver': [[1, 0, [1], False, 'A', True, 'ack-a', 1, None, None, None], [1, 0, [1], True, 'A', True, 'partition', None, None, None, None], [1, 0, [1], True, 'B', True, 'route', None, None, None, None], [1, 0, [1], True, 'B', True, 'delivery-blocked', None, None, None, None], [1, 0, [1], True, 'B', True, 'read', None, 0, True, False], [1, 0, [1], False, 'B', True, 'partition', None, None, None, None], [1, 1, [], False, 'B', True, 'delivered', None, None, None, None], [1, 1, [], False, 'B', True, 'read', None, 1, True, True]], 'two-writes-one-delivery': [[1, 0, [1], False, 'A', True, 'ack-a', 1, None, None, None], [2, 0, [1, 2], False, 'A', True, 'ack-a', 2, None, None, None], [2, 1, [2], False, 'A', True, 'delivered', None, None, None, None], [2, 1, [2], False, 'B', True, 'route', None, None, None, None], [2, 1, [2], False, 'B', True, 'read', None, 1, True, False]], 'invalid-target': [], 'unknown-operation': [], 'invalid-write': [], 'invalid-partition': [], 'unavailable-b': [[1, 0, [1], False, 'A', True, 'ack-a', 1, None, None, None], [1, 0, [1], False, 'A', False, 'availability', None, None, None, None], [1, 0, [1], False, 'B', False, 'route', None, None, None, None]], 'execution-failure': None}
REASONS={'invalid-target': 'invalid target', 'unknown-operation': 'unknown operation', 'invalid-write': 'invalid value', 'invalid-partition': 'invalid partition', 'unavailable-b': 'unavailable:B'}
FIXTURES={'baseline': {'steps': [{'op': 'read'}]}, 'ack-a': {'steps': [{'op': 'write', 'value': 'v1'}, {'op': 'read'}]}, 'failover-before-delivery': {'steps': [{'op': 'write', 'value': 'v1'}, {'op': 'route', 'target': 'B'}, {'op': 'read'}]}, 'delivered-before-failover': {'steps': [{'op': 'write', 'value': 'v1'}, {'op': 'deliver'}, {'op': 'route', 'target': 'B'}, {'op': 'read'}]}, 'partition-read': {'steps': [{'op': 'write', 'value': 'v1'}, {'op': 'partition', 'enabled': True}, {'op': 'route', 'target': 'B'}, {'op': 'deliver'}, {'op': 'read'}]}, 'heal-deliver': {'steps': [{'op': 'write', 'value': 'v1'}, {'op': 'partition', 'enabled': True}, {'op': 'route', 'target': 'B'}, {'op': 'deliver'}, {'op': 'read'}, {'op': 'partition', 'enabled': False}, {'op': 'deliver'}, {'op': 'read'}]}, 'two-writes-one-delivery': {'steps': [{'op': 'write', 'value': 'v1'}, {'op': 'write', 'value': 'v2'}, {'op': 'deliver'}, {'op': 'route', 'target': 'B'}, {'op': 'read'}]}, 'invalid-target': {'steps': [{'op': 'route', 'target': 'C'}]}, 'unknown-operation': {'steps': [{'op': 'promote'}]}, 'invalid-write': {'steps': [{'op': 'write', 'value': True}]}, 'invalid-partition': {'steps': [{'op': 'partition', 'enabled': 'yes'}]}, 'unavailable-b': {'steps': [{'op': 'write', 'value': 'v1'}, {'op': 'availability', 'target': 'B', 'available': False}, {'op': 'route', 'target': 'B'}, {'op': 'read'}]}, 'execution-failure': {'rawInput': '{"steps":'}}
CONTRACT={'initial': {'A': [0, 'v0'], 'B': [0, 'v0'], 'router': 'A', 'partition': False, 'available': ['A', 'B']}, 'writer': 'A only; ack after local in-memory update and enqueue', 'delivery': 'one FIFO head per explicit deliver, blocked by partition; no auto delivery', 'freshness': 'read revision equals A revision at that read step', 'observation': 'last successful read of successful run; refusal/failure has no normal answer', 'time': 'ordered step indices, no real clock', 'bounds': '1..20 steps; values nonempty strings <=32 chars; exact bool'}

def sha(b):return hashlib.sha256(b).hexdigest()
def check(root=R):
 run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text())
 assert (run/'stdout.json').read_bytes()==(run/'result.json').read_bytes()
 for n,h in d['sourceHashes'].items():assert sha((root/n).read_bytes())==h,n
 for n,v in json.loads((run/'artifacts.json').read_text())['files'].items():
  b=(run/n).read_bytes();assert len(b)==v['bytes'] and sha(b)==v['sha256'],n
 assert json.loads((root/'oracle.json').read_text())=={'contract':CONTRACT,'tables':TABLES,'refusals':REASONS}
 assert json.loads((root/'fixtures.json').read_text())==FIXTURES
 assert [c['id'] for c in d['cases']]==list(FIXTURES)
 for c in d['cases']:
  name=c['id'];folder=run/name;x=FIXTURES[name]
  expectedInput=x['rawInput'].encode() if 'rawInput' in x else (json.dumps(x,sort_keys=True)+'\n').encode()
  assert (folder/'input.txt').read_bytes()==expectedInput and sha(expectedInput)==c['inputSha256']
  assert (folder/'stdout.txt').read_text()==c['stdout'] and (folder/'stderr.txt').read_text()==c['stderr']
  if name=='execution-failure':
   assert c['exitCode']==3 and c['outcome']=='execution-failure' and c['observation'] is None and c['stdout']==''
   assert c['stderr'].startswith('JSONDecodeError:') and 'line 1 column 10 (char 9)' in c['stderr'];continue
  o=json.loads(c['stdout']);assert o==c['observation'] and c['stderr']==''
  refused=name in REASONS;assert c['exitCode']==(2 if refused else 0) and c['outcome']==('refusal' if refused else 'normal')
  assert o['accepted'] is (not refused) and o['reason']==REASONS.get(name)
  assert len(o['trace'])==len(TABLES[name]);reads=[];acks=[]
  for i,(observed,hand) in enumerate(zip(o['trace'],TABLES[name])):
   a,b,q,partition,target,bUp,status,ackRev,readRev,available,fresh=hand
   # All fixture values are literal v0/v1/v2; not inferred by replaying worker.
   stores={'A':{'revision':a,'value':'v'+str(a),'available':True},'B':{'revision':b,'value':'v'+str(b),'available':bUp}}
   queue=[{'revision':v,'value':'v'+str(v)} for v in q]
   ack=None if ackRev is None else {'store':'A','revision':ackRev,'value':'v'+str(ackRev),'scope':'local model ack; no B/durability guarantee'}
   reading=None if readRev is None else {'step':i,'store':target,'available':available,'revision':readRev,'value':'v'+str(readRev),'requiredRevision':a,'fresh':fresh}
   expected={'step':i,'operation':x['steps'][i],'status':status,'stores':stores,'deliveryQueue':queue,'partition':partition,'router':target,'ack':ack,'read':reading}
   assert observed==expected,(name,i,observed,expected)
   if reading is not None:reads.append(reading)
   if ack is not None:acks.append(ack)
  assert o['reads']==reads and o['acks']==acks and o['answer']==(None if refused else reads[-1])
  if refused:assert o['failedStep']==len(TABLES[name])
 return len(d['cases'])
if __name__=='__main__':check();print('PASS 13 fixtures; independent hand revision/delivery/read/ack tables, refusals and execution failure')

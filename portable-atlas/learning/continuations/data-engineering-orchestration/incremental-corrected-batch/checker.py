#!/usr/bin/env python3
import hashlib,json,pathlib,sqlite3
ROOT=pathlib.Path(__file__).resolve().parent
INITIAL=[['a',100],['b',200],['c',300]]
FINAL=[['a',110],['c',300],['d',400]]
SPECS={'replace':[(0,[['a',110],['d',400]],510,None)],'append':[(0,[['a',100],['a',110],['b',200],['c',300],['d',400]],1110,None)],'keyed':[(0,FINAL,810,None),(0,FINAL,810,None)],'unknown-delete':[(2,INITIAL,600,'unknown-delete:z')],'duplicate-id':[(2,INITIAL,600,'duplicate-event-id:e1')],'id-collision':[(0,FINAL,810,None),(2,FINAL,810,'event-id-payload-conflict:e1')],'same-key-order':[(0,[['a',120],['c',300],['d',400]],820,None)],'same-key-reverse':[(0,FINAL,810,None)]}
ORDERS={'replace':[['e1','e2','e3']],'append':[['e1','e2','e3']],'keyed':[['e1','e2','e3'],['e1','e2','e3']],'unknown-delete':[['e1','e5']],'duplicate-id':[['e1','e1']],'id-collision':[['e1','e2','e3'],['e1']],'same-key-order':[['e1','e2','e3','e4']],'same-key-reverse':[['e4','e1','e2','e3']]}
EVENTS={'e1':{'eventId':'e1','op':'upsert','key':'a','price':110,'sourceVersion':2},'e2':{'eventId':'e2','op':'delete','key':'b','sourceVersion':2},'e3':{'eventId':'e3','op':'upsert','key':'d','price':400,'sourceVersion':1},'e4':{'eventId':'e4','op':'upsert','key':'a','price':120,'sourceVersion':3},'e5':{'eventId':'e5','op':'delete','key':'z','sourceVersion':1}}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dbread(p):
 c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.execute('PRAGMA query_only=ON');rows=[list(x) for x in c.execute('SELECT key,price FROM items ORDER BY key,price')];ledger=[list(x) for x in c.execute('SELECT event_id,payload_sha FROM applied ORDER BY event_id')];c.close();return rows,ledger
def check(run):
 d=json.loads((run/'result.json').read_text());assert json.loads((run/'stdout.json').read_text())==d
 for n,h in json.loads((run/'artifacts.json').read_text()).items():assert (run/n).stat().st_size==h['bytes'] and digest(run/n)==h['sha256'],n
 for n,h in d['sourceHashes'].items():assert digest(ROOT/n)==h,n
 assert digest(run/'worker.py')==digest(ROOT/'worker.py') and digest(run/'expectations.json')==digest(ROOT/'expectations.json')
 assert json.loads((run/'initial.json').read_text())==INITIAL,'initial input literal'
 expectations=json.loads((run/'expectations.json').read_text());assert expectations['initial']==INITIAL
 expected={name:[dict(exit=code,rows=rows,sum=total,**({'reason':reason} if reason else {})) for code,rows,total,reason in specs] for name,specs in SPECS.items()};assert expectations['results']==expected,'prior literal expectations'
 assert [c['id'] for c in d['cases']]==list(SPECS)
 for c in d['cases']:
  name=c['id'];folder=run/name;strategy=name if name in ['replace','append'] else 'keyed';assert c['strategy']==strategy and c['initial']==INITIAL
  assert dbread(folder/'before.sqlite')==(INITIAL,[]) and digest(folder/'before.sqlite')==c['beforeDbSha256'];assert len(c['attempts'])==len(SPECS[name]);previous=INITIAL;priorHash=c['beforeDbSha256']
  for i,(a,(code,rows,total,reason)) in enumerate(zip(c['attempts'],SPECS[name])):
   o=a['observation'];assert a['exitCode']==o['exitCode']==code and o['reason']==reason,'exit/refusal literal';assert o['before']==previous and o['after']==rows and o['count']==len(rows) and o['sum']==total,'independent rows/count/sum'
   assert a['argv']==['python3','-B','worker.py','--db',name+'/data.sqlite','--input',name+'/batch-'+str(i)+'.json','--strategy',strategy]
   assert a['stderr']==(folder/('stderr-'+str(i)+'.txt')).read_text()=='';assert a['stdout']==(folder/('stdout-'+str(i)+'.json')).read_text() and json.loads(a['stdout'])==o
   events=json.loads((folder/('batch-'+str(i)+'.json')).read_text());assert events==o['events'] and digest(folder/('batch-'+str(i)+'.json'))==a['inputSha256'];assert o['order']==[e['eventId'] for e in events]==ORDERS[name][i],'order contract'
   for e in events:
    expectedEvent=dict(EVENTS[e['eventId']])
    if name=='id-collision' and i==1:expectedEvent['price']=999
    assert e==expectedEvent,'event input literal'
   db=folder/('after-'+str(i)+'.sqlite');assert dbread(db)==(rows,o['ledger']);assert digest(db)==a['afterDbSha256'] and a['beforeDbSha256']==priorHash
   ids=[] if strategy!='keyed' or name in ['unknown-delete','duplicate-id'] else (['e1','e2','e3','e4'] if name.startswith('same-key') else ['e1','e2','e3']);assert [x[0] for x in o['ledger']]==ids,'ledger IDs'
   for eid,h in o['ledger']:assert hashlib.sha256(json.dumps(EVENTS[eid],sort_keys=True,separators=(',',':')).encode()).hexdigest()==h,'event payload binding'
   up='INSERT INTO items(key,price) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET price=excluded.price'; plain='INSERT INTO items(key,price) VALUES(?,?)'; delete='DELETE FROM items WHERE key=?'
   common=[(up,['a',110]),(delete,['b']),(up,['d',400])]
   contracts={'replace':[('DELETE FROM items',[]),(plain,['a',110]),(plain,['d',400])],'append':[(plain,['a',110]),(plain,['d',400])],'keyed':common if i==0 else [],'unknown-delete':[(up,['a',110])],'duplicate-id':[],'id-collision':common if i==0 else [],'same-key-order':common+[(up,['a',120])],'same-key-reverse':[(up,['a',120])]+common}
   actualMutations=[(e['sql'],e['params']) for e in o['sqlTrace'] if e['sql'].startswith('INSERT INTO items') or e['sql'].startswith('DELETE FROM items')]
   assert actualMutations==contracts[name],'actual SQL operation order'
   assert a['startedUtc']<=a['endedUtc']
   if code==2:assert a['beforeDbSha256']==a['afterDbSha256'],'refusal preserves DB'
   if name=='keyed' and i==1:assert a['beforeDbSha256']==a['afterDbSha256'] and [x['action'] for x in o['actions']]==['already-applied']*3,'replay idempotence'
   if name=='unknown-delete':assert o['sqlTrace'][-3]['sql']=='ROLLBACK','atomic rollback'
   previous=rows;priorHash=a['afterDbSha256']
  assert dbread(folder/'data.sqlite')==(previous,c['attempts'][-1]['observation']['ledger']) and digest(folder/'data.sqlite')==priorHash
 return d
if __name__=='__main__':check(ROOT/(ROOT/'CURRENT').read_text().strip());print('PASS 8 cases / 10 attempts; independent literal rows/count/sum/order; closed DB and raw bindings')

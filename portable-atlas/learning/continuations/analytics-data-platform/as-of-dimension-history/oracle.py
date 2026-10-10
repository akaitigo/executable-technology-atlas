# SPDX-License-Identifier: Apache-2.0
# Hand ledger is independent of SQLite and model. Version assignment is authored by order id.
EXPECTED={
 'boundary':('OK',[(1,'MATCHED'),(2,'MATCHED')],{'north':100,'south':50}),
 'latest-fault':('OK',[(2,'MATCHED'),(2,'MATCHED')],{'south':150}),
 'gap':('OK',[(None,'GAP'),(2,'MATCHED')],{'GAP':100,'south':50}),
 'unknown-key':('OK',[(1,'MATCHED'),(None,'UNKNOWN_KEY')],{'north':100,'UNKNOWN_KEY':50}),
 'overlap':('REFUSED_MULTIPLE_MATCH',[([1,2],'MULTIPLE_MATCH')],None),
 'invalid-interval':('REFUSED_INVALID_INPUT',[],None),
 'execution-failure':('EXECUTION_FAILURE',[],None)}
def check(name,result):
 status,assignment,aggregate=EXPECTED[name]
 raw={
  'boundary':[['o1','c1',9,100,1,'north'],['o2','c1',10,50,2,'south']],
  'latest-fault':[['o1','c1',9,100,2,'south'],['o2','c1',10,50,2,'south']],
  'gap':[['o1','c1',9,100,None,None],['o2','c1',10,50,2,'south']],
  'unknown-key':[['o1','c1',9,100,1,'north'],['o2','c9',10,50,None,None]],
  'overlap':[['o1','c1',9,100,1,'north'],['o2','c1',10,50,1,'north'],['o2','c1',10,50,2,'south']],
  'invalid-interval':[],'execution-failure':[]}
 assert result['rows']==raw[name],(name,'raw rows')
 assert result['status']==status,(name,'status')
 assert result['aggregate']==aggregate,(name,'aggregate')
 if name=='overlap':
  assert result['orders']==[dict(id='o1',time=9,amount=100,classification='MATCHED',versions=[1],regions=['north']),dict(id='o2',time=10,amount=50,classification='MULTIPLE_MATCH',versions=[1,2],regions=['north','south'])]
 elif status=='OK':
  assert len(result['orders'])==2
  for i,(version,kind) in enumerate(assignment):
   o=result['orders'][i]
   assert o['id']==['o1','o2'][i] and o['amount']==[100,50][i] and o['time']==[9,10][i]
   assert o['classification']==kind and o['versions']==([] if version is None else [version])
   assert o['regions']==([] if version is None else ['north' if version==1 else 'south'])
 else:assert result['orders']==[] and result['rows']==[]
 if name=='execution-failure':assert 'OperationalError' in result['reason'] and 'absent_column' in result['reason']
 return True
# Explicit tick ledger: t0..9 old, t10..19 new, t20 gap (half-open endpoint).
TICKS=[1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,None]

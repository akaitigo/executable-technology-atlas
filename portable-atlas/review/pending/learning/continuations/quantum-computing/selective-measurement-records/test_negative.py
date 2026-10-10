import json,copy,subprocess,sys
from pathlib import Path
from oracle import check
P=Path(__file__).resolve().parent

def collect():
 ptr=json.loads((P/'evidence/current.json').read_text());data=json.loads((P/'evidence'/ptr['raw']).read_text());a=next(x for x in data['attempts'] if x['id']=='biased-discard')['raw'];out=a['result'];inp=json.loads(a['input_json']);mut=[]
 def changed(name,path,value,base=out,x=inp):
  m=copy.deepcopy(base);node=m
  for k in path[:-1]:node=node[k]
  node[path[-1]]=value;mut.append((name,m,x))
 changed('wrong probability',['branches',0,'p'],'1/2');changed('sigma normalized early',['branches',0,'sigma','density'],out['branches'][0]['conditional']['density']);changed('normalization omitted',['branches',0,'conditional'],out['branches'][0]['sigma']);changed('conditional trace',['branches',0,'conditional','trace'],'9/25');changed('wrong branch H coherence',['branches',1,'after_h','density',0,1],['1/2','0']);changed('lost branch status',['branches',0,'status'],'UNREACHABLE')
 for key in ['weighted','direct','h_of_weighted','h_of_direct','weighted_after_h']:
  changed(key+'/density',['discard',key,'density',0,1],['1','0']);changed(key+'/trace',['discard',key,'trace'],'0')
 changed('equal weights disguised',['faults','equal_weights','full_equal'],True);changed('equal H probabilities',['faults','equal_weights','h_probabilities_equal'],False);changed('omit trace disguised',['faults','omit_normalization','density','trace'],'1');changed('selection state mismatch',['selection','state'],out['branches'][0]['conditional'])
 z=next(x for x in data['attempts'] if x['id']=='zero-record-1')['raw'];changed('zero branch fabricated',['branches',1,'conditional'],out['branches'][1]['conditional'],z['result'],json.loads(z['input_json']));changed('zero branch assigned probability',['branches',1,'p'],'1/2',z['result'],json.loads(z['input_json']));changed('zero fault hidden',['faults','zero_division','status'],'NO_FAILURE_IN_THIS_CASE',z['result'],json.loads(z['input_json']))
 detected=[]
 for name,m,x in mut:
  try:check(m,x)
  except AssertionError:detected.append(name)
 rho=inp['rho'];bads=[]
 def bad(name,r=None,record='discard',reason='DENSITY'):
  bads.append((name,dict(rho=r if r is not None else rho,record=record),reason))
 bad('record-bool',record=True,reason='RECORD');bad('record-range',record=2,reason='RECORD');bad('trace-two',[[['1','0'],['0','0']],[['0','0'],['1','0']]]);bad('not-hermitian',[[['1/2','0'],['1/4','0']],[['0','0'],['1/2','0']]]);bad('negative-determinant',[[['1/2','0'],['1','0']],[['1','0'],['1/2','0']]]);bad('negative-diagonal',[[['-1','0'],['0','0']],[['0','0'],['2','0']]]);bad('component-integer',[[[1,0],['0','0']],[['0','0'],['0','0']]],reason='COMPONENT');bad('zero-denominator',[[['1/0','0'],['0','0']],[['0','0'],['0','0']]],reason='COMPONENT');bads.append(('extra',dict(inp,shot=0),'SCHEMA'));bads.append(('malformed-json',None,'SCHEMA'));invalid=[]
 for name,x,reason in bads:
  r=subprocess.run([sys.executable,'-B','model.py'],cwd=P,input=json.dumps(x) if x is not None else '{',text=True,capture_output=True);o=json.loads(r.stdout);invalid.append(dict(id=name,exit=r.returncode,result=o,passed=r.returncode==2 and o==dict(status='INPUT_REFUSED',reason=reason)))
 return dict(status='passed' if len(detected)==len(mut) and all(x['passed'] for x in invalid) else 'failed',mutants=len(mut),detected=detected,schema=invalid,probability_only_blind_spot=out['faults']['equal_weights']['h_probabilities_equal'] and not out['faults']['equal_weights']['full_equal'])
if __name__=='__main__':
 x=collect()
 if sys.argv[1:]==['--record']:(P/'evidence/negative.json').write_text(json.dumps(x,indent=2)+'\n')
 print(json.dumps(x));sys.exit(0 if x['status']=='passed' else 1)

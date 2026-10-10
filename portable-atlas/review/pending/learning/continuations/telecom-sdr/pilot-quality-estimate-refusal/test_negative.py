import copy,json,sys,subprocess
from pathlib import Path
from oracle import check,compare
P=Path(__file__).resolve().parent

def collect():
 ptr=json.loads((P/'evidence/current.json').read_text());raw=json.loads((P/'evidence'/ptr['raw']).read_text());cases=json.loads((P/'fixture.json').read_text());base=raw['attempts'][0]['raw'];out=base['result'];inp=json.loads(base['input_json']);muts=[]
 for k,v in [('h',['-1','0']),('h2','0'),('known_energy','0'),('rx_energy','99'),('sse','1'),('normalized_residual','1')]:
  m=copy.deepcopy(out);m['stats'][k]=v;muts.append((k,m,inp))
 for k in ['magnitude_pass','residual_pass']:
  m=copy.deepcopy(out);m['gates'][k]=False;muts.append((k,m,inp))
 for k,v in [('fit',['0','0']),('residual',['1','0']),('correlation',['0','0']),('residual_energy','1')]:
  m=copy.deepcopy(out);m['rows'][0][k]=v;muts.append(('row/'+k,m,inp))
 for name in ['gated','naive']:
  for k,v in [('status','REFUSED'),('reasons',['FALSE']),('factor',['-1','0']),('corrected',[['0','0']]*4),('decisions',[1]*4),('demodulated',False)]:
   m=copy.deepcopy(out);m['policies'][name][k]=v;muts.append((name+'/'+k,m,inp))
 refused=next(x for x in raw['attempts'] if x['id']=='magnitude-below')['raw'];m=copy.deepcopy(refused['result']);m['policies']['gated']['decisions']=[0]*4;muts.append(('refused-demodulated',m,json.loads(refused['input_json'])))
 detected=[]
 for name,m,x in muts:
  try:check(m,x)
  except AssertionError:detected.append(name)
 # 有限harnessの境界:拒否にBER0、比較4、成功受信を捏造すると独立再算術と一致しない。
 audits=[]
 for id,k,v in [('magnitude-below','ber','0'),('magnitude-below','compared_bits',4),('magnitude-below','verdict','ACCEPTED_CORRECT'),('inverse-pilot-consistent','error_count',0),('inverse-pilot-consistent','ber','0')]:
  a=next(x for x in raw['attempts'] if x['id']==id);truth=next(c['truth'] for c in cases if c['id']==id);m=copy.deepcopy(a['harness']);m['policies']['gated'][k]=v;audits.append(dict(id=id,field=k,detected=m!=compare(a['raw']['result'],truth)))
 bads=[('integer-coordinate',dict(inp,pilot_rx=[[1,0]]*4),'COMPONENT'),('truth-leak',dict(inp,truth=[0,1,0,1]),'SCHEMA'),('shape',dict(inp,pilot_rx=[]),'SCHEMA'),('bool',dict(inp,min_gain_sq=True),'COMPONENT'),('float',dict(inp,max_residual=.5),'COMPONENT'),('zero-denominator',dict(inp,min_gain_sq='1/0'),'COMPONENT'),('negative-threshold',dict(inp,min_gain_sq='-1'),'THRESHOLD_RANGE'),('large-coordinate',dict(inp,pilot_rx=[['5','0']]*4),'COORDINATE_RANGE'),('malformed-json',None,'SCHEMA')];invalid=[]
 for name,x,reason in bads:
  r=subprocess.run([sys.executable,'-B','model.py'],cwd=P,input=json.dumps(x) if x is not None else '{',text=True,capture_output=True);o=json.loads(r.stdout);invalid.append(dict(id=name,exit=r.returncode,result=o,passed=r.returncode==2 and o==dict(status='INPUT_REFUSED',reason=reason)))
 return dict(status='passed' if len(detected)==len(muts) and all(x['passed'] for x in invalid) and all(x['detected'] for x in audits) else 'failed',mutants=len(muts),detected=detected,harness_mutants=audits,schema=invalid)
if __name__=='__main__':
 r=collect()
 if sys.argv[1:]==['--record']:(P/'evidence/negative.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r));sys.exit(0 if r['status']=='passed' else 1)

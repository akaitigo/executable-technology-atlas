"""Atlas: fixed hand tables and component formulas check saved calculations only."""
import argparse,copy,hashlib,json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def flat(a):return [v for row in a for v in row]
def shaped(a):return [a[:2],a[2:]]
def pair(a):return [str(a[0]),str(a[1])]
def scaled(a,w):return [[[str(F(v)*w) for v in cell] for cell in row] for row in a]
def h_closed(a):
 # Pauli coordinates: H maps (x,y,z) to (z,-y,x).
 x=2*F(a[0][1][0]);y=-2*F(a[0][1][1]);z=F(a[0][0][0])-F(a[1][1][0])
 return [[[str((1+x)/2),'0'],[str(z/2),str(y/2)]],[[str(z/2),str(-y/2)],[str((1-x)/2),'0']]]
def expected_stage(a,eigen):
 u,v=F(a[0][0][0]),F(a[1][1][0]);real,imag=map(F,a[0][1]);assert not(real and imag),'fixed axes only'
 return {'density':a,'trace':str(u+v),'hermitian':a[0][0][1]=='0' and a[1][1][1]=='0' and a[1][0]==[str(real),str(-imag)],'positive_semidefinite':True,'determinant':str(u*v-real*real-imag*imag),'eigenvalues':eigen,'coherence_z':str(abs(real)+abs(imag)),'rho01':a[0][1],'purity':str(u*u+v*v+2*(real*real+imag*imag)),'probabilities_z':[str(u),str(v)]}
def check(r,o,fixture):
 assert r['status']=='observed' and r['priority_observed']==10 and r['shots']==0 and r['quantum_hardware_used'] is False and r['browser_executed'] is False
 assert len(r['cases'])==9 and len(r['wrong_phase_flip'])==2
 inputs={s['id']:s['rho'] for s in fixture['states']};zeros=[[['0','0'],['0','0']],[['0','0'],['0','0']]];p0=[[['1','0'],['0','0']],[['0','0'],['0','0']]];p1=[[['0','0'],['0','0']],[['0','0'],['1','0']]]
 zero_branches=0
 for actual,expected in zip(r['cases'],o['rows']):
  name,p=expected['state'],expected['p'];rho=inputs[name];e=shaped(expected['after_e']);h=shaped(expected['after_h'])
  assert actual['case_id']==name+'@'+p and actual['state_id']==name and actual['p']==p and actual['equivalent_phase_flip_q']==str(F(p)/2)
  # Independently derive off-diagonal shrink and H action, not model.py import.
  derived=copy.deepcopy(rho)
  for i,j in [(0,1),(1,0)]:derived[i][j]=[str(F(v)*(1-F(p))) for v in rho[i][j]]
  assert derived==e and h_closed(e)==h
  assert actual['before']==expected_stage(rho,['0','1'])
  assert actual['after_e']==expected_stage(e,expected['eigenvalues'])
  assert actual['after_h']==expected_stage(h,expected['eigenvalues'])
  assert actual['after_e']['coherence_z']==expected['coherence_e'] and actual['after_h']['coherence_z']==expected['coherence_h']
  for k in ['determinant','purity']:assert actual['after_e'][k]==expected[k] and actual['after_h'][k]==expected[k]
  assert len(actual['branches'])==3
  for i,(b,w) in enumerate(zip(actual['branches'],expected['weights'])):
   weight=F(w);conditional=[rho,p0,p1][i] if weight else None;after=h_closed(conditional) if weight else None
   expected_branch={'branch':['unchanged','Z-result-0','Z-result-1'][i],'weight':w,'reachable':bool(weight),'conditional':conditional,'after_h_conditional':after,'contribution':scaled(conditional,weight) if weight else zeros,'after_h_contribution':scaled(after,weight) if weight else zeros,'observed_measurement_record':False}
   assert b==expected_branch,(name,p,i);zero_branches+=int(weight==0)
  assert actual['branch_sum']==e and actual['branch_sum_after_h']==h and actual['branch_weights_sum']=='1' and actual['paths_equal'] is True and actual['shots']==0 and actual['quantum_hardware_used'] is False
 assert zero_branches==11
 for actual,expected in zip(r['wrong_phase_flip'],o['wrong_phase_flip']):
  p=expected['p_mistaken_as_q'];e=shaped(expected['after_e']);h=shaped(expected['after_h']);eig=['1/2','1/2'] if p=='1/2' else ['0','1']
  assert actual['p_mistaken_as_q']==p and actual['meaning']=='phase_flip_probability; not intended E_p' and actual['matches_intended'] is False and actual['hardware_failure'] is False
  assert actual['after_e']==expected_stage(e,eig) and actual['after_h']==expected_stage(h,eig) and h_closed(e)==h
  for k in ['determinant','purity']:assert actual['after_e'][k]==expected[k]
  assert actual['after_e']['coherence_z']==expected['coherence_e']
 expected_refusals=[('extra_key','input_keys'),('bool_schema','schema'),('basis_reversed','basis'),('p_is_phase_flip','channel_semantics'),('bool_p','rational_type'),('float_p','rational_type'),('negative_p','p_range'),('p_over_one','p_range'),('unsupported_p','p_not_fixed'),('zero_denominator','rational_syntax'),('matrix_shape','matrix_shape'),('complex_shape','complex_shape'),('not_hermitian','not_hermitian'),('wrong_trace','trace_not_one'),('negative_eigenvalue','not_positive_semidefinite'),('unknown_state','state_id'),('shots_not_zero','shots')]
 assert r['input_refusals']==[{'case':n,'status':'expected_refusal','reason':why} for n,why in expected_refusals]
 return True
def mutations(r,o,f):
 edits=[('lost_case',lambda z:z['cases'].pop()),('wrong_parameter_meaning',lambda z:z['cases'][1].__setitem__('equivalent_phase_flip_q','1/2')),('wrong_coherence',lambda z:z['cases'][1]['after_e'].__setitem__('coherence_z','0')),('imaginary_sign',lambda z:z['cases'][4]['after_h']['density'][0][1].__setitem__(1,'-1/4')),('only_probabilities_match',lambda z:z['cases'][4]['after_e']['density'][0][1].__setitem__(1,'0')),('zero_branch_normalized',lambda z:z['cases'][0]['branches'][1].__setitem__('conditional',f['states'][2]['rho'])),('weights_averaged',lambda z:z['cases'][1]['branches'][1].__setitem__('weight','1/3')),('trace_forged',lambda z:z['cases'][0]['after_e'].__setitem__('trace','0')),('negative_eigenvalue',lambda z:z['cases'][1]['after_e'].__setitem__('eigenvalues',['-1/4','5/4'])),('fake_measurement_record',lambda z:z['cases'][1]['branches'][0].__setitem__('observed_measurement_record',True)),('wrong_channel_accepted',lambda z:z['wrong_phase_flip'][1].__setitem__('matches_intended',True)),('shots_claimed',lambda z:z.__setitem__('shots',100))]
 out=[]
 for name,edit in edits:
  altered=copy.deepcopy(r);edit(altered)
  try:check(altered,o,f)
  except (AssertionError,KeyError,TypeError,IndexError):out.append({'case':name,'detected':True})
  else:raise AssertionError('undetected modification: '+name)
 return out
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);p.add_argument('--save',action='store_true');a=p.parse_args();d=ROOT/a.run;r=json.loads((d/'result.json').read_text());report=json.loads((d/'report.json').read_text());o=json.loads((ROOT/'hand-oracle.json').read_text());fixture=json.loads((ROOT/'fixtures.json').read_text());check(r,o,fixture)
 assert r['fixture_sha256']==sha(ROOT/'fixtures.json') and report['status']=='observed' and report['child_reaped'] is True and report['exit_code']==0
 assert json.loads((d/'stdout.txt').read_text())==r
 source_map_path=ROOT/'observations/execution-source-map.json'
 source_map=json.loads(source_map_path.read_text()) if source_map_path.exists() else None
 if source_map:
  assert source_map['run']==a.run and source_map['report_sha256']==sha(d/'report.json')
  assert source_map['result_sha256']==sha(d/'result.json') and set(source_map['files'])==set(report['sources'])
 for n,h in report['sources'].items():
  measured=ROOT/source_map['files'][n]['path'] if source_map else ROOT/n
  assert measured.resolve().is_relative_to(ROOT.resolve()) and sha(measured)==h,n
  if source_map:assert source_map['files'][n]['sha256']==h,n
 for n in ['stdout','stderr']:assert sha(d/(n+'.txt'))==report[n+'_sha256']
 assert report['result_sha256']==sha(d/'result.json') and report['priority_guard']['observed_nice']==10 and report['priority_guard']['ready'] is True
 assert sha(ROOT/report['resource_gate_file'])==report['resource_gate_sha256']
 x={'title':'Atlas saved partial-dephasing calculation verification','passed':True,'normal_cases':9,'normal_density_stages':27,'branches':27,'zero_weight_branches':11,'wrong_parameter_cases':2,'input_refusals':17,'mutation_checks':mutations(r,o,fixture),'source_files':len(report['sources']),'result_sha256':sha(d/'result.json'),'producer_reexecuted':False,'quantum_hardware_used':False,'browser_executed':False}
 x.update(measured_source_resolution='explicit saved snapshot' if source_map else 'current source',source_map_sha256=sha(source_map_path) if source_map else None,verifier_current_sha256=sha(Path(__file__)),future_guard_executed=False)
 if a.save:(ROOT/'observations/calculation-verification.json').write_text(json.dumps(x,indent=2)+'\n')
 print(json.dumps(x))
if __name__=='__main__':main()

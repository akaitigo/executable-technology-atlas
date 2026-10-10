"""Reject misleading saved outcomes and check finite declared input boundaries."""
import copy,json
from pathlib import Path
from oracle import validate as verify
from producer import validate,Refused,FIXTURE,run
ROOT=Path(__file__).resolve().parent
def checks():
 pointer=json.loads((ROOT/'evidence/current.json').read_text());raw=json.loads((ROOT/'evidence'/pointer['raw']).read_text());rejected=[]
 mutations=[('missing_reverse_as_no_impact',5,'reachable',[]),('automatic_reverse_repair',5,'reachable',['D-CAP','R-CAP','T-CAP']),('missing_link_as_normal',4,'status','NORMAL'),('FIFO_mixed_into_capacity',0,'reachable',['D-CAP','D-FIFO','R-CAP','R-FIFO','T-CAP','T-FIFO']),('execution_failure_as_normal',17,'status','NORMAL'),('orphan_not_reported',4,'missing_reverse',[])]
 for name,case,key,value in mutations:
  r=copy.deepcopy(raw);r['cases'][case][key]=value
  try:verify(r)
  except AssertionError:rejected.append(name)
  else:raise AssertionError('accepted '+name)
 base={k:copy.deepcopy(FIXTURE[k]) for k in ['nodes','forward','reverse']};probes=[]
 def refusal(name,g,d,start,reason):
  try:validate(g,d,start)
  except Refused as e:assert str(e)==reason,(name,str(e));probes.append(name)
  else:raise AssertionError('accepted '+name)
 refusal('graph_type',[], 'forward','R-CAP','GRAPH_TYPE')
 g=copy.deepcopy(base);g['nodes'][0]['text']=7;refusal('node_field_type',g,'forward','R-CAP','NODE_TYPE')
 g=copy.deepcopy(base);g['nodes'].append(g['nodes'][0]);refusal('duplicate_node',g,'forward','R-CAP','DUPLICATE_ID')
 g=copy.deepcopy(base);g['nodes'].pop();refusal('missing_node',g,'forward','R-CAP','NODE_SET')
 refusal('bad_direction',base,'sideways','R-CAP','DIRECTION')
 refusal('start_non_string',base,'forward',7,'UNKNOWN_ID')
 assert run('unknown-case')['status']=='INPUT_REFUSED' and run('unknown-case')['reason']=='UNKNOWN_CASE';probes.append('unknown_case')
 return dict(oracle_mutations_rejected=rejected,input_boundary_probes=probes)
if __name__=='__main__':print(json.dumps(checks()))

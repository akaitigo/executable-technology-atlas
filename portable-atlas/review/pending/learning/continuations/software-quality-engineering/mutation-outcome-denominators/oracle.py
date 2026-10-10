# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
H=json.loads((Path(__file__).parent/'hand-oracle.json').read_text())
def config(f,fold):return dict(report=[dict(id='m'+str(i+1),status=s) for i,s in enumerate(f['statuses'])],fold=fold)
def check(r,f,fold):
 assert r['inputs']==config(f,fold) and r['status']=='REPORT_AGGREGATED';assert r['synthetic_report'] and not r['runner_executed'] and not r['timeout_executed']
 status_groups={'Killed':['detected','covered','valid','total'],'Timeout':['detected','covered','valid','total'],'Survived':['undetected','covered','valid','total'],'NoCoverage':['undetected','valid','total'],'RuntimeError':['invalid','total'],'CompileError':['invalid','total'],'Ignored':['total'],'Pending':['total']}
 for name,values,fracs,do_fold in [('canonical',f['canonical'],f['fractions'],False),('reported',f['folded'] if fold else f['canonical'],f['folded_fractions'] if fold else f['fractions'],fold)]:
  a=r[name];assert [a['metrics'][k] for k in H['metric_order']]==values
  statuses=['Survived' if do_fold and s in ['RuntimeError','CompileError','Ignored','Pending'] else s for s in f['statuses']]
  assert a['counts']=={s:statuses.count(s) for s in H['statuses']}
  for g in H['metric_order']:assert a['group_ids'][g]==['m'+str(i+1) for i,s in enumerate(statuses) if g in status_groups[s]]
  for key,den,frac in zip(H['ratio_order'],[values[3],values[2],values[5]],fracs):
   q=a['ratios'][key];assert q['numerator']==values[0] and q['denominator']==den and q['fraction']==frac and q['defined']==(den!=0);assert q['percent']==(round(values[0]/den*100,6) if den else None)
 expected=[]
 for i,s in enumerate(f['statuses']):
  target='Survived' if fold and s in ['RuntimeError','CompileError','Ignored','Pending'] else s;expected.append(dict(id='m'+str(i+1),source_status=s,reported_status=target,changed=s!=target,canonical_groups=status_groups[s]))
 assert r['classifications']==expected

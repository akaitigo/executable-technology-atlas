# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import datetime,json,platform
from fractions import Fraction
STATES=('Killed','Survived','NoCoverage','Timeout','RuntimeError','CompileError','Ignored','Pending')
GROUPS={'detected':('Killed','Timeout'),'undetected':('Survived','NoCoverage'),'covered':('Killed','Timeout','Survived'),'valid':('Killed','Timeout','Survived','NoCoverage'),'invalid':('RuntimeError','CompileError'),'total':STATES}
def ratio(n,d):
 return dict(numerator=n,denominator=d,fraction=str(Fraction(n,d)) if d else None,percent=round(100*n/d,6) if d else None,defined=d!=0)
def aggregate(rows):
 counts={s:sum(r['status']==s for r in rows) for s in STATES};ids={k:[r['id'] for r in rows if r['status'] in statuses] for k,statuses in GROUPS.items()};metrics={k:len(v) for k,v in ids.items()};d=metrics['detected']
 return dict(counts=counts,group_ids=ids,metrics=metrics,ratios={k:ratio(d,metrics[den]) for k,den in [('mutation_score','valid'),('covered_score','covered'),('detected_over_total_context_only','total')]})
def evaluate(config):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();out=dict(inputs=config,status='REFUSED_INPUT',started_utc=start,ended_utc=start,canonical=None,reported=None,classifications=[],runner_executed=False,timeout_executed=False,synthetic_report=True,python=platform.python_version())
 if type(config) is not dict or set(config)!=set(['report','fold']) or type(config['fold']) is not bool or type(config['report']) is not list or len(config['report'])>8:return out
 ids=[]
 for row in config['report']:
  if type(row) is not dict or set(row)!=set(['id','status']) or type(row['id']) is not str or row['id'] not in ['m'+str(i) for i in range(1,9)] or row['id'] in ids or type(row['status']) is not str or row['status'] not in STATES:return out
  ids.append(row['id'])
 rows=config['report'];folded=[dict(id=r['id'],status='Survived' if config['fold'] and r['status'] in ['RuntimeError','CompileError','Ignored','Pending'] else r['status']) for r in rows]
 out.update(status='REPORT_AGGREGATED',canonical=aggregate(rows),reported=aggregate(folded),classifications=[dict(id=r['id'],source_status=r['status'],reported_status=f['status'],changed=r['status']!=f['status'],canonical_groups=[g for g,s in GROUPS.items() if r['status'] in s]) for r,f in zip(rows,folded)],ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());return out
if __name__=='__main__':print(json.dumps(evaluate({'report':[dict(id='m'+str(i+1),status=s) for i,s in enumerate(STATES)],'fold':False}),indent=2))

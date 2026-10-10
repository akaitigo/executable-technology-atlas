# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import datetime,os,platform
from cases import FIXTURES,valid
from chaining import Chaining
from list_oracle import list_trace
def evaluate(config):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 if not valid(config):return dict(status='REFUSED_INPUT',inputs=config,trace=[],oracle=[],differences=[],total_comparisons=None,total_moves=None)
 ops=FIXTURES[config['fixture']];table=Chaining(config['policy'],config['mode']);expected=list_trace(ops);rows=[];diff=[]
 for i,op in enumerate(ops):
  row=table.step(op);row['step']=i+1;actual=dict(found=row['found'],value=row['value'],action=row['action'],entries=sorted([pair for b in row['after'] for pair in b]))
  row['list_oracle']=expected[i];row['logical_match']=actual==expected[i];row['actual_logical']=actual;rows.append(row)
  if not row['logical_match']:diff.append(i+1)
 return dict(status='EXECUTED',inputs=config,trace=rows,oracle=expected,differences=diff,total_comparisons=sum(x['key_comparisons'] for x in rows),total_moves=sum(x['move_count'] for x in rows),final_capacity=len(table.buckets),final_entries=sorted([pair for b in table.buckets for pair in b]),started_utc=start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),system=platform.system(),pid=os.getpid()),cost_unit='logical operations, not elapsed time')

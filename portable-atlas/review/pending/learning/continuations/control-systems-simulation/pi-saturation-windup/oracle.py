# SPDX-License-Identifier: Apache-2.0
import json,math
from pathlib import Path
from decimal import Decimal
from decimal_oracle import expected
HAND=json.loads((Path(__file__).parent/'hand-oracle.json').read_text())
def near(a,b):return math.isfinite(float(a)) and abs(float(a)-float(b))<=1e-10*max(1.,abs(float(b)))
def equal(a,b):
 if b is None or type(b) in [str,bool]:assert type(a) is type(b) and a==b
 elif type(b) is dict:
  assert set(a)==set(b)
  for k in b:equal(a[k],b[k])
 elif type(b) is list:
  assert len(a)==len(b)
  for x,y in zip(a,b):equal(x,y)
 else:assert type(a) in [int,float] and near(a,b)
def check(r):
 assert r['status']=='EXECUTED';rows,metrics=expected(r['inputs']);equal(r['rows'],rows);equal(r['metrics'],metrics)
 assert HAND['fixed_before_implementation']
 hand=next(x for x in HAND['initial'] if float(x['h'])==r['inputs']['h'] and x['mode']==r['inputs']['mode'] and x['ki']==r['inputs']['ki'])
 aliases={'requested':'u_requested','actual':'u_actual','stop':'integral_stopped'}
 for actual,want in zip(r['rows'][:3],hand['rows']):
  for k,v in want.items():
   if type(v) is bool:assert actual[aliases.get(k,k)]==v
   else:assert near(actual[aliases.get(k,k)],v)
 assert len(r['rows'])==int(8/r['inputs']['h'])+1
 for row in r['rows'][:-1]:
  assert near(row['e'],row['r']-row['y']) and near(row['u_requested'],row['e']+r['inputs']['ki']*row['z'])
  if r['inputs']['mode']!='free':assert -1<=row['u_actual']<=1
 assert all(r['rows'][-1][k] is None for k in ['u_requested','u_actual','clipped','integral_stopped','y_next','z_next'])
def check_probe(actual,probe):
 aliases={'requested':'u_requested','actual':'u_actual','stop':'integral_stopped'}
 for k in ['y','z','r','e','requested','actual','stop','z_next']:
  equal(actual[aliases.get(k,k)],probe[k])
 with __import__('decimal').localcontext() as c:
  c.prec=70;u=Decimal(str(probe['actual']));y=Decimal(str(probe['y']));yn=u+(y-u)*(-Decimal('.5')).exp()
  assert near(actual['y_next'],yn)

# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import datetime,platform,os
from cases import valid
from controller import step
from metrics import measure
def evaluate(config):
 if not valid(config):return dict(status='REFUSED_INPUT',inputs=config,rows=[],metrics=None)
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();h=config['h'];n=int(8/h);y=z=0.;rows=[]
 for i in range(n):
  t=i*h;row=step(y,z,4. if t<4. else .5,h,config['mode'],config['ki']);row.update(step=i,t=t);rows.append(row);y,z=row['y_next'],row['z_next']
 rows.append(dict(step=n,t=8.,r=.5,y=y,z=z,e=.5-y,u_requested=None,u_actual=None,clipped=None,integral_stopped=None,y_next=None,z_next=None))
 return dict(status='EXECUTED',inputs=config,rows=rows,metrics=measure(rows,h),started_utc=start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),system=platform.system(),pid=os.getpid()),model=dict(plant='dy/dt=(u-y)/tau',tau=1.,kp=1.,limits=[-1.,1.],horizon=8.,switch_time=4.,reference=[4.,.5],initial=[0.,0.],plant_update='held input exact exponential; floating point',controller_update='discrete old-state rectangular integration',solver_error_claim='no Euler truncation error used; float roundoff still exists'))

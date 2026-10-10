# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import datetime,platform,os
from cases import FIXTURES,valid
from motion import calculate
def evaluate(c):
 if not valid(c):return dict(status='REFUSED_INPUT',inputs=c,rows=[],events=[])
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();f=FIXTURES[c['fixture']];spec={k:f[k] for k in ['v','tau','a','obstacle_m','horizon_s']};spec['h']=c['h'];result=calculate(spec,c['mode']);result.update(status='EXECUTED',inputs=c,physics_inputs=spec,started_utc=start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),system=platform.system(),pid=os.getpid()),scope='ideal finite 1D counterfactual free trajectory; contact response not simulated');return result

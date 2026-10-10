"""UIの合成pilot操作。receiverへは構築後のI/Qだけを送る。真のbitsなし。"""
import copy
from fractions import Fraction as F

def prepare(inp,controls):
 x=copy.deepcopy(inp);s=F(controls.get('scale') or '1');a=F(controls.get('noise') or '0')
 if abs(s)>2 or abs(a)>2:raise ValueError('construction range')
 for i,p in enumerate(x['pilot_rx']):x['pilot_rx'][i]=[str(s*F(p[0])+a*(1 if i<2 else -1)),str(s*F(p[1]))]
 for k in ['min_gain_sq','max_residual']:
  if controls.get(k):x[k]=controls[k]
 return x

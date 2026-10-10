# SPDX-License-Identifier: Apache-2.0
from fractions import Fraction as F
def validate(c):
 x=c.get('X');y=c.get('y');l=c.get('lambda_value')
 if type(l) is not int or not 0<=l<=4:raise ValueError('lambda integer 0..4')
 if not isinstance(x,list) or not 2<=len(x)<=4 or any(not isinstance(r,list) or len(r)!=2 for r in x):raise ValueError('X shape')
 if any(type(v) is not int or not -5<=v<=5 for r in x for v in r):raise ValueError('X integers -5..5')
 if not any(v for r in x for v in r):raise ValueError('zero matrix outside contract')
 if not isinstance(y,list) or len(y)!=len(x) or any(type(v) is not int or not -20<=v<=20 for v in y):raise ValueError('y shape/integer/range')
 if c.get('fault') not in ('none','divide-zero'):raise ValueError('fault option')
def rref(matrix,ncols):
 a=[[F(v) for v in r] for r in matrix];row=0;piv=[]
 for col in range(ncols):
  found=next((i for i in range(row,len(a)) if a[i][col]),None)
  if found is None:continue
  a[row],a[found]=a[found],a[row];v=a[row][col];a[row]=[z/v for z in a[row]]
  for i in range(len(a)):
   if i!=row:
    v=a[i][col];a[i]=[z-v*q for z,q in zip(a[i],a[row])]
  piv.append(col);row+=1
  if row==len(a):break
 return a,piv
def objective(c,w):
 predicted=[sum(F(x)*v for x,v in zip(row,w)) for row in c['X']];residuals=[F(y)-p for y,p in zip(c['y'],predicted)];rss=sum(v*v for v in residuals);norm=sum(v*v for v in w);penalty=c['lambda_value']*norm
 return dict(predicted=list(map(str,predicted)),residuals=list(map(str,residuals)),rss=str(rss),norm=str(norm),penalty=str(penalty),objective=str(rss+penalty))
def run(c):
 try:validate(c)
 except ValueError as e:return dict(status='REFUSED_INPUT',reason=str(e),solution=None)
 try:
  if c['fault']=='divide-zero':F(1,0)
  x=c['X'];y=c['y'];l=c['lambda_value'];g=[[sum(F(r[i])*r[j] for r in x) for j in range(2)] for i in range(2)];b=[sum(F(r[i])*v for r,v in zip(x,y)) for i in range(2)];a=[[g[i][j]+(l if i==j else 0) for j in range(2)] for i in range(2)]
  _,xp=rref(x,2);reduced,piv=rref([a[i]+[b[i]] for i in range(2)],2)
  coef=[F(0),F(0)]
  for i,p in enumerate(piv):coef[p]=reduced[i][-1]
  basis=[]
  for free in range(2):
   if free not in piv:
    vec=[F(0),F(0)];vec[free]=F(1)
    for i,p in enumerate(piv):vec[p]=-reduced[i][free]
    basis.append(vec)
  witnesses=[dict(coef=list(map(str,[coef[i]+t*basis[0][i] for i in range(2)])),**objective(c,[coef[i]+t*basis[0][i] for i in range(2)])) for t in range(-2,3)] if basis else [dict(coef=list(map(str,coef)),**objective(c,coef))]
  return dict(status='NON_UNIQUE' if basis else 'UNIQUE',reason='valid OLS family, not execution failure' if basis else '',solution=dict(rank_x=len(xp),rank_system=len(piv),gram=[[str(v) for v in row] for row in g],rhs=list(map(str,b)),system=[[str(v) for v in row] for row in a],det=str(a[0][0]*a[1][1]-a[0][1]*a[1][0]),rref=[[str(v) for v in row] for row in reduced],coef=list(map(str,coef)),null_basis=[list(map(str,v)) for v in basis],witnesses=witnesses,**objective(c,coef)))
 except ArithmeticError as e:return dict(status='EXECUTION_FAILURE',reason=type(e).__name__+': '+str(e),solution=None)

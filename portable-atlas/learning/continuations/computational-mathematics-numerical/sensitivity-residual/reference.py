"""Independent Cramer closed form using Fraction; does not import float solver."""
from fractions import Fraction as F
def norm(v):return max(map(abs,v))
def closed(a,b):
    determinant=a[0][0]*a[1][1]-a[0][1]*a[1][0]
    return [(b[0]*a[1][1]-a[0][1]*b[1])/determinant,(a[0][0]*b[1]-b[0]*a[1][0])/determinant]
def residual(a,x,b):return [a[i][0]*x[0]+a[i][1]*x[1]-b[i] for i in range(2)]
def vector(v):return [str(x) for x in v]
def scalar(x):return dict(exact=str(x),float=float(x))
def reference(f,r):
    if not r['solver_started']:return None
    e=F(f['epsilon']);delta=F(f['delta']);ad=[[F(1),F(1)],[F(1),1+e]];bd=[F(2),2+e];bp=[bd[0],bd[1]+delta];xd=closed(ad,bp)
    af=[[F.from_float(v) for v in row] for row in r['A']];bf=[F.from_float(v) for v in r['b_original']];bpf=[F.from_float(v) for v in r['b_perturbed']];xf=closed(af,bpf);xfbase=closed(af,bf);actual=[F.from_float(v) for v in r['x_float_perturbed']]
    decimal_change=[x-1 for x in xd];dinput=[bp[i]-bd[i] for i in range(2)]
    return dict(decimal=dict(A=[vector(row) for row in ad],b_original=vector(bd),b_perturbed=vector(bp),x_baseline=['1','1'],x_perturbed=vector(xd),change=vector(decimal_change),change_inf=str(norm(decimal_change)),input_change_inf=str(norm(dinput)),input_relative_change_inf=str(norm(dinput)/norm(bd)),solution_relative_change_inf=str(norm(decimal_change)),directional_relative_amplification=str(norm(decimal_change)/(norm(dinput)/norm(bd))),condition_inf=str((2+e)**2/e),residual_perturbed=vector(residual(ad,xd,bp)),residual_original=vector(residual(ad,xd,bd))),float_inputs=dict(A=[vector(row) for row in af],b_original=vector(bf),b_perturbed=vector(bpf),x_baseline=vector(xfbase),x_perturbed=vector(xf),change=vector([xf[i]-xfbase[i] for i in range(2)])),computed=dict(forward_error_decimal_inf=scalar(norm([actual[i]-xd[i] for i in range(2)])),forward_error_float_inputs_inf=scalar(norm([actual[i]-xf[i] for i in range(2)])),oracle_conversion_shift_inf=scalar(norm([xd[i]-xf[i] for i in range(2)])),distance_from_original_inf=scalar(norm([x-1 for x in actual])),exact_residual_decimal_perturbed=vector(residual(ad,actual,bp)),exact_residual_decimal_original=vector(residual(ad,actual,bd)),exact_residual_float_perturbed=vector(residual(af,actual,bpf)),exact_residual_float_original=vector(residual(af,actual,bf))))

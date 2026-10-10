"""Authored fixed non-singular 2x2 float Gaussian elimination; no oracle imports."""
def inf(v):return max(abs(x) for x in v)
def residual(a,x,b):return [sum(a[i][j]*x[j] for j in range(2))-b[i] for i in range(2)]
def solve(a,b):
    factor=a[1][0]/a[0][0];pivot=a[1][1]-factor*a[0][1];rhs=b[1]-factor*b[0]
    second=rhs/pivot;first=(b[0]-a[0][1]*second)/a[0][0]
    return [first,second],[dict(event='eliminate',factor=factor,pivot=pivot,rhs=rhs),dict(event='back_substitute',x=[first,second])]
def experiment(fixture):
    if fixture['epsilon'] not in ('0.1','0.0001') or fixture['delta']!='0.000001':return dict(status='INPUT_REJECTED',reason='EPSILON_OUTSIDE_FIXED_DOMAIN',solver_started=False)
    epsilon=float(fixture['epsilon']);delta=float(fixture['delta']);a=[[1.0,1.0],[1.0,1.0+epsilon]];original=[1.0,1.0];b=[sum(row[j]*original[j] for j in range(2)) for row in a];perturbed=[b[0],b[1]+delta]
    base,t0=solve(a,b);changed,t1=solve(a,perturbed);change=[changed[i]-base[i] for i in range(2)];input_change=[perturbed[i]-b[i] for i in range(2)];rp=residual(a,changed,perturbed);ro=residual(a,changed,b);distance=inf([changed[i]-original[i] for i in range(2)])
    bad=fixture['judgment']=='residual-only';claims=inf(rp)<=1e-12;near=distance<=1e-6
    return dict(status='BAD_JUDGMENT' if bad else 'SOLVED',solver_started=True,A=a,b_original=b,b_perturbed=perturbed,x_original=original,x_float_baseline=base,x_float_perturbed=changed,float_metrics=dict(input_change_inf=inf(input_change),input_relative_change_inf=inf(input_change)/inf(b),solution_change_inf=inf(change),solution_relative_change_inf=inf(change)/inf(base),distance_from_original_inf=distance,residual_perturbed=rp,residual_perturbed_inf=inf(rp),residual_original=ro,residual_original_inf=inf(ro)),trace=dict(baseline=t0,perturbed=t1),bad_judgment=dict(enabled=bad,rule='residual_inf <= 1e-12 implies original_distance_inf <= 1e-6',claims_original_near=claims if bad else None,actually_original_near=near,bad_rule_failed=bad and claims and not near))

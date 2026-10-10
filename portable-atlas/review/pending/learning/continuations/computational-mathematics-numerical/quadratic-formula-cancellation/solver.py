import math
METHODS=('standard','product')
def solve(a,b,c,method,mutant=None):
    if type(method) is not str or method not in METHODS: raise ValueError('unknown method')
    if any(type(v) not in (int,float) for v in (a,b,c)): raise ValueError('int/float only; bool refused')
    try: a,b,c=map(float,(a,b,c))
    except OverflowError: raise ValueError('coefficient overflow')
    if not all(math.isfinite(v) for v in (a,b,c)): raise ValueError('nonfinite coefficient')
    if a==0: raise ValueError('a=0 excluded')
    bb=b*b;ac4=4*a*c;disc=bb-ac4;denom=2*a
    if not all(math.isfinite(v) for v in (bb,ac4,disc,denom)) or denom==0:
        raise ValueError('unsupported intermediate range')
    if disc<0: raise ValueError('negative float discriminant')
    s=math.sqrt(disc)
    steps=dict(bb=bb,ac4=ac4,discriminant=disc,sqrt=s,denominator=denom)
    if method=='standard':
        if mutant=='wrong_denominator': roots=[((-b-s)/2)*a,((-b+s)/2)*a]
        else: roots=[(-b-s)/denom,(-b+s)/denom]
    else:
        sign=math.copysign(s,b)
        if mutant=='wrong_q_sign': sign=-sign
        q=-0.5*(b+sign)
        if mutant=='abs_b_sign': q=-0.5*(abs(b)+s)
        steps['q']=q
        if not math.isfinite(q): raise ValueError('nonfinite q')
        if q==0:
            if b==0 and c==0 and mutant!='drop_zero_special':
                roots=[0.,0.];steps['special']='double zero'
            else: raise ValueError('q=0 outside special case')
        else:
            roots=[q/a,c/(a*q) if mutant=='wrong_product' else c/q]
            if c==0 and mutant=='zero_c_return_one': roots=[q/a,1.]
    if not all(math.isfinite(v) for v in roots): raise ValueError('nonfinite root')
    return dict(method=method,roots=sorted(roots),steps=steps)

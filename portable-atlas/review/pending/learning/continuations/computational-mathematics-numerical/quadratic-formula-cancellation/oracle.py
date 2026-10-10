"""Fraction coefficients/residual and high precision symmetric root formula.
Does not import float solver or reproduce its q path.
"""
from decimal import Decimal,localcontext
from fractions import Fraction
def dec(f): return Decimal(f.numerator)/Decimal(f.denominator)
def original(fixture):
    u,v=map(Fraction,fixture['roots']);a=Fraction(fixture['scale'])
    return (a,-a*(u+v),a*u*v),sorted([u,v])
def high_roots(coefficients,precision):
    a,b,c=coefficients;d=b*b-4*a*c
    if d<0: raise ValueError('exact discriminant negative')
    with localcontext() as ctx:
        ctx.prec=precision
        radical=dec(d).sqrt();aa=dec(a);bb=dec(b)
        return sorted([(-bb-radical)/(2*aa),(-bb+radical)/(2*aa)])
def checked_roots(coefficients):
    low=high_roots(coefficients,160);high=high_roots(coefficients,240)
    with localcontext() as ctx:
        ctx.prec=90
        assert [+v for v in low]==[+v for v in high], 'precision cross-check'
    return low
def residual(coefficients,x):
    a,b,c=coefficients
    value=a*x*x+b*x+c
    terms=abs(a)*x*x+abs(b)*abs(x)+abs(c)
    norm=abs(a)+abs(b)+abs(c)
    return dict(signed=str(value),absolute=str(abs(value)),
                term_scaled=str(abs(value)/terms) if terms else None,
                coefficient_scaled=str(abs(value)/norm) if norm else None)

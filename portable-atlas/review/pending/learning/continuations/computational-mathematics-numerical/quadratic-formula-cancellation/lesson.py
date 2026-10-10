from decimal import Decimal,localcontext
from fractions import Fraction
from oracle import original,checked_roots,residual,dec
from solver import solve
def display(value):
    if value is None:return None
    with localcontext() as ctx:
        ctx.prec=100
        return format(dec(value) if isinstance(value,Fraction) else value,'.35g')
def run(fixture,method):
    coeff,known=original(fixture)
    floats=list(map(float,coeff));rounded=tuple(Fraction.from_float(v) for v in floats)
    roots=checked_roots(rounded)
    result=solve(*floats,method)
    metrics=[]
    with localcontext() as ctx:
        ctx.prec=100
        for k,(x,truth,reference) in enumerate(zip(result['roots'],known,roots)):
            xf=Fraction.from_float(x);xd=dec(xf);td=dec(truth)
            total=abs(xd-td);arithmetic=abs(xd-reference)
            metrics.append(dict(index=k,computed=x,original_root=str(truth),rounded_coefficient_root=str(reference),
                total_abs=display(total),total_rel=display(total/abs(td)) if td else None,
                arithmetic_abs=display(arithmetic),arithmetic_rel=display(arithmetic/abs(reference)) if reference else None,
                conversion_root_abs=display(abs(reference-td)),
                residual_original=residual(coeff,xf),residual_rounded=residual(rounded,xf)))
    differences=[]
    for before,after in zip(coeff,rounded):
        differences.append(dict(signed=str(after-before),absolute=str(abs(after-before)),relative=str(abs((after-before)/before)) if before else None))
    return dict(fixture=fixture['id'],original_coefficients=[str(v) for v in coeff],
                float_coefficients=floats,float_hex=[v.hex() for v in floats],
                rounded_coefficients_exact=[str(v) for v in rounded],coefficient_differences=differences,
                oracle_precision=[160,240],oracle_matching_digits=90,**result,metrics=metrics)

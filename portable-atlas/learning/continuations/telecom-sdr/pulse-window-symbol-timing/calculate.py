from fractions import Fraction
def calculate(f,offset):
    if type(offset) is not int or offset not in (0,1):raise ValueError('finite offset contract')
    x=f['impulses'];h=f['pulse'];length=len(x)+len(h)-1
    windows=[[offset+2*k,offset+2*k+1] for k in range(3)]
    missing=sorted({i for w in windows for i in w if i>=length})
    if missing and not f['padding']:return dict(status='INSUFFICIENT_WINDOW',missing_indices=missing,convolution_started=False)
    y=[0]*length;products=[]
    for i,a in enumerate(x):
        for j,b in enumerate(h):
            y[i+j]+=a*b
            products.append(dict(input_index=i,pulse_index=j,output_index=i+j,product=a*b,running_sum=y[i+j]))
    rows=[];bits=[];strict=[];means=[]
    for indices in windows:
        values=[y[i] if i<length else 0 for i in indices]
        mean=Fraction(sum(values),2);means.append(str(mean))
        normal=0 if mean>0 else 1 if mean<0 else None
        bit=0 if normal is None and f['zero_policy']=='bit0' else normal
        strict.append(normal);bits.append(bit)
        rows.append(dict(indices=indices,values=values,provenance=['convolution' if i<length else 'declared_zero_padding' for i in indices],sum=sum(values),mean={'numerator':mean.numerator,'denominator':mean.denominator,'exact':str(mean)},decision=bit))
    bad=bits!=strict
    status=('BAD_ACCEPTED' if bad else 'FAULT_CONTROL') if f['zero_policy']=='bit0' else 'WINDOWED_ERASURE' if None in bits else 'WINDOWED'
    return dict(status=status,convolution_started=True,samples=y,products=products,windows=windows,means=means,decisions=bits,strict_decisions=strict,padded_indices=missing,rule_failed=bad,rows=rows,known_transmitted_bits=[0,1,0])

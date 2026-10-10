# SPDX-License-Identifier: Apache-2.0
import math
VERSION='bell-classical-correlations-1';BASIS=['00','01','10','11'];TOL=1e-12
I=[[1,0],[0,1]];H=[[1/math.sqrt(2),1/math.sqrt(2)],[1/math.sqrt(2),-1/math.sqrt(2)]]
def pairs(value):
    if isinstance(value,list):return [pairs(v) for v in value]
    c=complex(value);return [c.real,c.imag]
def tensor(a,b):return [[x*y for x in rowa for y in rowb] for rowa in a for rowb in b]
def mv(a,v):return [sum(x*y for x,y in zip(row,v)) for row in a]
def outer(v):return [[a*b.conjugate() for b in v] for a in v]
def mm(a,b):return [[sum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]
def dagger(a):return [[a[j][i].conjugate() for j in range(len(a))] for i in range(len(a[0]))]
def rotate(rho,u):return mm(mm(u,rho),dagger(u))
def partial(rho,keep):
    if keep==0:return [[sum(rho[2*a+b][2*c+b] for b in [0,1]) for c in [0,1]] for a in [0,1]]
    return [[sum(rho[2*a+b][2*a+d] for a in [0,1]) for d in [0,1]] for b in [0,1]]
def cnot(control):
    matrix=[[0j]*4 for _ in range(4)]
    for col in range(4):
        a,b=divmod(col,2)
        if control==0:b^=a
        else:a^=b
        matrix[2*a+b][col]=1+0j
    return matrix

def density(branches):return [[sum(w*v[i]*v[j].conjugate() for w,v in branches) for j in range(4)] for i in range(4)]
def metrics(rho):
    trace=sum(rho[i][i] for i in range(4));square=mm(rho,rho)
    residual=max(abs(rho[i][j]-rho[j][i].conjugate()) for i in range(4) for j in range(4))
    return dict(trace=pairs(trace),purity=sum(square[i][i] for i in range(4)).real,hermitian_residual=residual,hermitian=residual<TOL,coherence_00_11=pairs(rho[0][3]),coherence_magnitude=abs(rho[0][3]))
def validate(f,basis):
    if not isinstance(f,dict):raise ValueError('fixture object required')
    if f.get('basis_order')!=BASIS:raise ValueError('basis order must be 00,01,10,11')
    if type(f.get('control')) is not int or f['control'] not in [0,1]:raise ValueError('control exact integer0/1')
    if f.get('method') not in ['circuit','mixture','branch-average','branch-average-renormalized','local-product']:raise ValueError('unknown preparation method')
    if basis not in ['Z','X']:raise ValueError('unknown measurement basis')
    w=f.get('weights')
    if not isinstance(w,list) or len(w)!=2 or any(type(x) not in (int,float) or not math.isfinite(x) or not 0<=x<=1 for x in w) or abs(sum(w)-1)>TOL:raise ValueError('finite probability weights summing1 required')
    values=f.get('initial')
    if not isinstance(values,list) or len(values)!=4 or any(type(x) not in (int,float) or not math.isfinite(x) for x in values):raise ValueError('finite real four-vector required')
    if abs(sum(x*x for x in values)-1)>TOL:raise ValueError('initial vector norm squared must be1')

def execute(f,basis):
    validate(f,basis);trace=[];method=f['method'];branches=None;v=None
    initial=[complex(x) for x in f['initial']];trace.append(dict(stage='initial',vector=pairs(initial),norm_squared=sum(abs(x)**2 for x in initial)))
    hfirst=tensor(H,I);hh=tensor(H,H);target_circuit=mv(cnot(0),mv(hfirst,initial));v00=[1+0j,0j,0j,0j];v11=[0j,0j,0j,1+0j]
    if method=='circuit':
        after_h=mv(hfirst,initial);trace.append(dict(stage='H_tensor_I',vector=pairs(after_h),norm_squared=sum(abs(x)**2 for x in after_h)))
        v=mv(cnot(f['control']),after_h);branches=[(1,v)];trace.append(dict(stage='CNOT',control=f['control'],vector=pairs(v),norm_squared=sum(abs(x)**2 for x in v)))
    elif method=='mixture':
        branches=list(zip(f['weights'],[v00,v11]));trace.append(dict(stage='classical_branches',weights=f['weights'],vectors=[pairs(v00),pairs(v11)],rule='weighted density sum, no vector averaging'))
    elif method.startswith('branch-average'):
        v=[f['weights'][0]*a+f['weights'][1]*b for a,b in zip(v00,v11)];trace.append(dict(stage='wrong_vector_average',vector=pairs(v),norm_squared=sum(abs(x)**2 for x in v)))
        if method.endswith('renormalized'):
            norm=math.sqrt(sum(abs(x)**2 for x in v));v=[x/norm for x in v];trace.append(dict(stage='wrong_average_renormalized',vector=pairs(v),note='valid pure vector now, but changes mixture semantics'))
        branches=[(1,v)]
    else:
        bell=outer(target_circuit);rho=tensor(partial(bell,0),partial(bell,1));trace.append(dict(stage='wrong_local_product',note='same reduced states do not recover full correlations'))
    if branches is not None:rho=density(branches)
    prepared=metrics(rho);reduced=[partial(rho,k) for k in [0,1]]
    intended=density(list(zip(f['weights'],[v00,v11]))) if method in ['mixture','branch-average','branch-average-renormalized'] else outer(target_circuit)
    intended_equal=max(abs(rho[i][j]-intended[i][j]) for i in range(4) for j in range(4))<TOL
    trace.append(dict(stage='prepared_density',density=pairs(rho),reduced=[pairs(x) for x in reduced],metrics=prepared))
    valid=prepared['hermitian'] and abs(complex(*prepared['trace'])-1)<TOL
    norm_info=[dict(weight=w,norm_squared=sum(abs(x)**2 for x in v)) for w,v in branches] if branches is not None else None
    if not valid:
        trace.append(dict(stage='reject_measurement',reason='prepared density trace is not1; no probability normalization'))
        return dict(id=f['id'],basis=basis,status='REJECTED',comparison_to_intended='REJECTED',branch_norms=norm_info,prepared_density=pairs(rho),prepared_reduced=[pairs(x) for x in reduced],prepared_metrics=prepared,measurement_density=None,measurement_reduced=None,measurement_metrics=None,joint_probabilities=None,marginal_probabilities=None,trace=trace)
    measured=rho if basis=='Z' else rotate(rho,hh);m=metrics(measured);prob=[measured[i][i].real for i in range(4)]
    marginals=[[prob[0]+prob[1],prob[2]+prob[3]],[prob[0]+prob[2],prob[1]+prob[3]]]
    trace.append(dict(stage='basis_rotation',basis=basis,operation='I4' if basis=='Z' else 'H_tensor_H',density=pairs(measured),metrics=m))
    trace.append(dict(stage='joint_Born',probabilities=prob,marginal_probabilities=marginals,shots=0,note='exact model probabilities up to floating error; no samples'))
    return dict(id=f['id'],basis=basis,status='MEASURED',comparison_to_intended='MATCH' if intended_equal else 'MISMATCH',branch_norms=norm_info,prepared_density=pairs(rho),prepared_reduced=[pairs(x) for x in reduced],prepared_metrics=prepared,measurement_density=pairs(measured),measurement_reduced=[pairs(partial(measured,k)) for k in [0,1]],measurement_metrics=m,joint_probabilities=prob,marginal_probabilities=marginals,trace=trace)

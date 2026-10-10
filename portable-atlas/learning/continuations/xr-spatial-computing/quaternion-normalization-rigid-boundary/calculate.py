from fractions import Fraction as F
def calculate(f,point_x):
    if type(point_x) is not int or point_x not in (1,2):raise ValueError('finite point contract')
    if any(type(a) is not int for a in f['q']):return dict(status='INPUT_REJECTED',reason='NONFINITE_QUATERNION',matrix_started=False)
    x,y,z,w=map(F,f['q']);s=x*x+y*y+z*z+w*w
    if not s:return dict(status='INPUT_REJECTED',reason='ZERO_QUATERNION',matrix_started=False)
    d=s if f['normalize'] else F(1)
    # Products of q/sqrt(s) are q_i*q_j/s; no irrational rounding here.
    R=[[1-2*(y*y+z*z)/d,2*(x*y-z*w)/d,2*(x*z+y*w)/d],[2*(x*y+z*w)/d,1-2*(x*x+z*z)/d,2*(y*z-x*w)/d],[2*(x*z-y*w)/d,2*(y*z+x*w)/d,1-2*(x*x+y*y)/d]]
    t=list(map(F,f['translation']));M=[R[i]+[t[i]] for i in range(3)]+[[F(0),F(0),F(0),F(1)]]
    gram=[[sum(R[k][i]*R[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    a,b,c=R[0];e,g,h=R[1];j,k,l=R[2];det=a*(g*l-h*k)-b*(e*l-h*j)+c*(e*k-g*j)
    world=[R[i][0]*point_x+t[i] for i in range(3)]+[F(1)];ds=sum((world[i]-t[i])**2 for i in range(3));rigid=gram==[[F(i==j) for j in range(3)] for i in range(3)] and det==1
    return dict(status='RIGID' if rigid else 'BAD_NONRIGID',matrix_started=True,norm_squared=str(s),normalization_divisor=str(d),normalization_enabled=f['normalize'],matrix_rows=[[str(a) for a in row] for row in M],matrix_column_major=[float(M[i][j]) for j in range(4) for i in range(4)],gram=[[str(a) for a in row] for row in gram],det=str(det),world=list(map(str,world)),distance_squared=str(ds),local_distance_squared=str(point_x*point_x),rigid=rigid,point=[point_x,0,0,1],origin=[0,0,0,1])

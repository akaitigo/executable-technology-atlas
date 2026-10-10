import copy,hashlib,json,math,pathlib
from fractions import Fraction as F
import oracle
ROOT=pathlib.Path(__file__).resolve().parent
def close(actual,expected):
    if isinstance(expected,list):assert len(actual)==len(expected);[close(a,e) for a,e in zip(actual,expected)];return
    assert type(actual) in (int,float) and math.isfinite(actual) and abs(actual-float(F(expected)))<=1e-10,(actual,expected)
def validate(key,v):
    c,x=key.split('@');x=int(x);e=oracle.inspect(key);r=v['result']
    assert v['case']==c and v['point_x']==x and v['fixture']==json.loads((ROOT/'fixtures.json').read_text())[c] and v['utc'].endswith('+00:00')
    assert set(v['source_binding'])=={'calculate.py','runner.py','fixtures.json','hand-oracle.json'}
    for n,d in v['source_binding'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d
    for k,a in e.items():
        if k!='inverse_rows':assert r[k]==a,(key,k)
    if not e['matrix_started']:assert r==e;return
    q=v['fixture']['q'];s=sum(a*a for a in q);assert r['norm_squared']==str(s) and r['normalization_divisor']==str(s if v['fixture']['normalize'] else 1)
    assert r['normalization_enabled']==v['fixture']['normalize'] and r['point']==[x,0,0,1] and r['origin']==[0,0,0,1]
    close(r['matrix_column_major'],[e['matrix_rows'][i][j] for j in range(4) for i in range(4)])
def browser_validate(v):
    key=v['case']+'@'+str(v['point_x']);validate(key,v);e=oracle.inspect(key);b=v['browser']
    assert v['browser_utc'].endswith('Z') and v['browser_user_agent'] and v['html_sha256']==hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest()
    if not e['matrix_started']:assert b==dict(status='NOT_RUN',dommatrix_started=False);return
    assert b['status']=='DOMMATRIX_OBSERVED' and b['dommatrix_started'] is True
    close(b['matrix_column_major'],[e['matrix_rows'][i][j] for j in range(4) for i in range(4)])
    close(b['inverse_column_major'],[e['inverse_rows'][i][j] for j in range(4) for i in range(4)])
    close(b['world'],e['world']);close(b['origin'],['2','3','0','1']);close(b['back'],[str(v['point_x']),'0','0','1'])
    close(b['gram'],e['gram']);close(b['det'],e['det']);close(b['distance_squared'],e['distance_squared']);assert b['rigid']==e['rigid'] and b['roundtrip_pass'] is True
def verify():
    rawpaths=sorted((ROOT/'observations').glob('*/raw.json'));assert rawpaths
    keys=set(json.loads((ROOT/'hand-oracle.json').read_text())['cases'])
    for p in rawpaths:
        raw=json.loads(p.read_text());assert set(raw)==keys
        for k,v in raw.items():validate(k,v)
    browserpaths=sorted((ROOT/'observations').glob('*/browser-*.json'))
    for p in browserpaths:browser_validate(json.loads(p.read_text()))
    if browserpaths:assert keys<={json.loads(p.read_text())['case']+'@'+str(json.loads(p.read_text())['point_x']) for p in browserpaths}
    rejected=[]
    for label,key,field,value in [('wrong quarterturn world','normalize-z90@1','world',['1','5','0','1']),('row-major serialization','normalize-z90@1','matrix_column_major',[0,-1,0,2,1,0,0,3,0,0,1,0,0,0,0,1]),('bad determinant accepted','bad-unit-assumption@1','det','1'),('bad rigid flag','bad-unit-assumption@1','rigid',True),('distance lost','bad-unit-assumption@1','distance_squared','1'),('zero started','zero@1','matrix_started',True)]:
        v=copy.deepcopy(raw[key]);v['result'][field]=value
        try:validate(key,v)
        except (AssertionError,KeyError):rejected.append(label);continue
        raise AssertionError('escaped '+label)
    if browserpaths:
        v=copy.deepcopy(json.loads(next(p for p in browserpaths if json.loads(p.read_text())['case']=='bad-unit-assumption').read_text()));v['browser']['rigid']=True
        try:browser_validate(v)
        except AssertionError:rejected.append('roundtrip incorrectly proves rigid')
        else:raise AssertionError('browser mutation escaped')
    return dict(strict_rigid=8,bad_nonrigid=2,expected_input_refusals=6,producer_runs=len(rawpaths),browser_records=len(browserpaths),mutants_rejected=rejected)
if __name__=='__main__':print(json.dumps(verify(),indent=2))

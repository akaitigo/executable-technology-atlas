# SPDX-License-Identifier: Apache-2.0
import argparse,copy,hashlib,json,math,platform,struct,sys,zlib,re
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
sys.dont_write_bytecode=True
import raster,route
HERE=Path(__file__).resolve().parent
SOURCE=['source.html','raster.py','verify.py','route.py','serve.py','fixtures.json','hand-oracle.json','index.html','README.md','VERIFICATION.md','coverage.json','sources.json','skills/atlas-perspective-correct-interpolation/SKILL.md']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def ray_oracle(f,point):
    # Independent camera-space geometry; no raster functions, reciprocal w or screen-barycentric UV formula.
    a,b,c=[[F(x) for x in row] for row in f['camera']];e=sub(b,a);g=sub(c,a);normal=cross(e,g);ray=[F(point[0]),F(point[1]),F(1)]
    den=dot(normal,ray);assert den!=0;t=dot(normal,a)/den;hit=[t*x for x in ray];d=sub(hit,a)
    # Solve camera triangle xy coordinates; plane intersection already supplies z.
    determinant=e[0]*g[1]-e[1]*g[0];beta=(d[0]*g[1]-d[1]*g[0])/determinant;gamma=(e[0]*d[1]-e[1]*d[0])/determinant;weights=[1-beta-gamma,beta,gamma]
    assert all(sum(weights[i]*F(f['camera'][i][j]) for i in range(3))==hit[j] for j in range(3))
    uv=[sum(weights[i]*F(f['uv'][i][j]) for i in range(3)) for j in range(2)]
    return dict(t=str(t),intersection=[str(x) for x in hit],world_weights=[str(x) for x in weights],uv=[str(x) for x in uv])
def expected_rgb(uv):
    if uv is None:return [18,28,44]
    u,v=map(F,uv)
    def rounded(x):q,r=divmod(x.numerator,x.denominator);return q+int(2*r>=x.denominator)
    tiles=[(8*x).numerator//(8*x).denominator for x in [u,v]]
    return [rounded(u*255),rounded(v*255),[40,220][sum(tiles)%2]]
def decode_png(data):
    assert data[:8]==b'\x89PNG\r\n\x1a\n';offset=8;compressed=b'';types=[];header=None
    while offset<len(data):
        n=int.from_bytes(data[offset:offset+4],'big');kind=data[offset+4:offset+8];payload=data[offset+8:offset+8+n];crc=int.from_bytes(data[offset+8+n:offset+12+n],'big');assert zlib.crc32(kind+payload)&0xffffffff==crc
        types.append(kind.decode());offset+=n+12
        if kind==b'IHDR':header=struct.unpack('>IIBBBBB',payload)
        elif kind==b'IDAT':compressed+=payload
        elif kind==b'IEND':assert not payload
        else:raise AssertionError(kind)
    assert types[0]=='IHDR' and types[-1]=='IEND' and offset==len(data);assert header==(16,16,8,2,0,0,0)
    decoded=zlib.decompress(compressed);assert len(decoded)==16*49
    pixels=[]
    for y in range(16):
        row=decoded[y*49:(y+1)*49];assert row[0]==0
        pixels.extend([list(row[k:k+3]) for k in range(1,49,3)])
    return pixels

def execute():
    fixtures=json.loads((HERE/'fixtures.json').read_text());hand=json.loads((HERE/'hand-oracle.json').read_text());runs=[]
    for f in fixtures:
        # Authored camera vertices are independent fixture, checked against projection contract.
        assert [[F(row[0])/F(row[2]),F(row[1])/F(row[2])] for row in f['camera']]==[[F(v) for v in row] for row in f['screen']]
        assert [row[2] for row in f['camera']]==f['w']
        run=raster.render(f);anchor=run['anchor'];oracle=ray_oracle(f,hand['screenpoint']);key='equal' if f['id']=='equal-w' else 'unequal'
        assert anchor['screen_weights']==hand['screen_weights'] and anchor['naive']==hand[key]['naive'] and anchor['correct']==hand[key]['correct']
        for k in ['t','world_weights']:assert oracle[k]==hand[key][k]
        assert oracle['uv']==anchor['correct'];anchor['oracle']=oracle
        for row in run['samples']:
            x,y=map(F,row['point']);covered=x+y<=1;assert row['covered']==covered
            assert row['screen_weights']==[str(1-x-y),str(x),str(y)]
            oracle=ray_oracle(f,row['point']);row['oracle']=oracle
            if covered:
                assert min(map(F,oracle['world_weights']))>=0 and row['normalized_weights']==oracle['world_weights'] and row['correct']==oracle['uv']
                assert sum(map(F,row['screen_weights']))==sum(map(F,row['normalized_weights']))==1
                assert row['naive']==[str(x+y),str(y)]
                if key=='equal':assert row['naive']==row['correct']
                else:assert row['naive']!=row['correct'] or x+y==1
            else:assert row['naive'] is row['correct'] is None
            na=expected_rgb(row['naive']);co=expected_rgb(oracle['uv'] if covered else None);diff=[abs(a-b) for a,b in zip(na,co)]
            assert row['colors']==dict(naive=na,correct=co,difference=diff)
        assert sum(r['covered'] for r in run['samples'])==136
        assert all(run['images'][kind][i]==row['colors'][kind] for i,row in enumerate(run['samples']) for kind in ['naive','correct','difference'])
        assert all(sum(map(F,r['point']))<=1 for r in run['samples'] if r['covered'])
        runs.append(run)
    base=fixtures[1];cases=[]
    def change(key,value):f=copy.deepcopy(base);f[key]=value;return f
    cases=[('object',None,['1/4','1/4']),('zero-w',change('w',[1,0,2]),[.25,.25]),('negative-w',change('w',[1,-1,2]),[.25,.25]),('bool-w',change('w',[1,True,2]),[.25,.25]),('nonfinite-w',change('w',[1,'nan',2]),[.25,.25]),('degenerate',change('screen',[[0,0],[1,0],[2,0]]),[.25,.25]),('vertex-count',change('screen',[[0,0],[1,0]]),[.25,.25]),('component-count',change('uv',[[0],[1,0],[1,1]]),[.25,.25]),('uv-range',change('uv',[[0,0],[2,0],[1,1]]),[.25,.25]),('nonfinite-screen',change('screen',[[0,0],['inf',0],[0,1]]),[.25,.25]),('zero-denominator',change('w',[1,'1/0',2]),[.25,.25]),('point-range',base,[-.1,.25]),('point-bool',base,[True,.25]),('point-nan',base,['nan',.25]),('point-length',base,[.25])]
    invalid=[]
    for name,f,point in cases:
        try:raster.sample(f,point)
        except ValueError as e:invalid.append(dict(id=name,input=f,point=point,status='EXPECTED_REFUSAL',error=str(e)))
        else:raise AssertionError(name)
    vertices=[]
    for point in [[0,0],[1,0],[0,1]]:
        result=raster.sample(base,point);assert result['naive']==result['correct'];vertices.append(result)
    return dict(runs=runs,vertex_boundaries=vertices,invalid_inputs=invalid,method='Fraction CPU producer vs camera ray-plane oracle; independent PNG decoder',samples=512,covered=272,background=240,scope='finite attribute interpolation; no GPU conformance',author_routing=dict(perspective=route.route('perspective'),gpu=route.route('gpu')))
def docs():
    for file in ['README.md','skills/atlas-perspective-correct-interpolation/SKILL.md']:
        for link in re.findall(r'\]\(([^)]+)\)',(HERE/file).read_text()):
            if not link.startswith(('https:','#')):assert ((HERE/file).parent/link.split('#')[0].split('?')[0]).resolve().exists(),link
    coverage=json.loads((HERE/'coverage.json').read_text());ids={s['id'] for s in json.loads((HERE/'sources.json').read_text())};assert 2<=len(coverage['next_experiments'])<=4
    for r in coverage['areas']+coverage['next_experiments']:assert r['source'] in ids

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--record');g.add_argument('--seal-record',action='store_true');args=p.parse_args();start=datetime.now(timezone.utc).isoformat();raw=execute();runname=args.record or 'attempt-01';folder=HERE/'observations'/runname
    if args.record:
        assert re.fullmatch(r'attempt-[0-9]+',runname);folder.mkdir(exist_ok=False)
        for r in raw['runs']:
            for kind,pixels in r['images'].items():(folder/(r['id']+'-'+kind+'.png')).write_bytes(raster.png(pixels))
        raw['attempt']=dict(command='python3 verify.py --record '+runname,started_at_utc=start,completed_at_utc=datetime.now(timezone.utc).isoformat(),exit_code=0,environment=dict(python=platform.python_version(),os=platform.system(),machine=platform.machine()),input_sha256=sha(HERE/'fixtures.json'),oracle_sha256=sha(HERE/'hand-oracle.json'),expected_refusal_count=15)
        (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
    else:
        saved=json.loads((folder/'raw.json').read_text());assert {k:v for k,v in saved.items() if k!='attempt'}==raw
    decoded=[]
    for r in raw['runs']:
        for kind,expected in r['images'].items():
            f=folder/(r['id']+'-'+kind+'.png');assert decode_png(f.read_bytes())==expected;decoded.append(dict(file=f.name,pixels=256,sha256=sha(f)))
    docs();sources={f:sha(HERE/f) for f in SOURCE};qa=json.loads((HERE/'observations/ui-qa.json').read_text())
    if qa['status']=='passed':
        for key,file in [('observed_ui_sha256','index.html'),('observed_sources_sha256','sources.json'),('observed_coverage_sha256','coverage.json')]:assert qa[key]==sha(HERE/file)
        assert qa['observed_raw_sha256']==sha(folder/'raw.json')
        matrix=json.loads((HERE/'observations/ui-matrix.json').read_text());observed=matrix['rows']
        assert len(observed)==10 and {(r['case'],r['sample']) for r in observed}=={(c,s) for c in ['equal-w','unequal-w'] for s in ['anchor',0,51,135,255]}
        assert len(matrix['expected_ui_refusals'])==5 and all(r['status'].startswith('拒否') and r['retained_point']==['1/4','1/4'] for r in matrix['expected_ui_refusals'])
        assert matrix['pixel51_colors']==raw['runs'][1]['samples'][51]['colors']
        for r in observed:
            actual=next(x for x in raw['runs'] if x['id']==r['case']);target=actual['anchor'] if r['sample']=='anchor' else actual['samples'][r['sample']]
            for k in ['covered','screen_weights','normalized_weights','naive','correct']:assert r[k]==target[k],(r,k)
    if args.record or args.seal_record:
        files=[f for f in folder.iterdir() if f.name!='receipt.json']+[f for f in (HERE/'observations').iterdir() if f.is_file() and f.name!='read-only-proof.json']
        receipt=dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py '+('--seal-record' if args.seal_record else '--record '+runname),exit_code=0,sources=sources,artifacts={str(f.relative_to(HERE)):sha(f) for f in files},decoded_png=decoded,checks=dict(camera_ray_oracle='passed',all_samples=512,independent_decoded_pixels=1536,expected_refusals=15,actual_iab=qa['status'],skill='author smoke; not independent AgentEval'))
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    else:
        receipt=json.loads((folder/'receipt.json').read_text());assert sources==receipt['sources']
        for f,h in receipt['artifacts'].items():assert sha(HERE/f)==h,f
    print(json.dumps(dict(status='passed',cases=2,samples=512,covered=272,background=240,decoded_png=6,decoded_pixels=1536,expected_refusals=15,record=args.record,seal_record=args.seal_record)))
if __name__=='__main__':main()

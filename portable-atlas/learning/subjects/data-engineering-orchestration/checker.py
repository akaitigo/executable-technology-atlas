"""Read-only, hand-row oracle; no producer imports."""
import argparse,csv,hashlib,io,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE='id,quantity,price\na,2,1.25\nb,1,0.10\na,2,1.25\nbad,nope,2.00\n'
ROWS=[['a',2,125,250],['b',1,10,10]]
SCHEMA={'version':1,'columns':[['id','string'],['quantity','integer'],['price_cents','integer'],['total_cents','integer']]}
def sha(b): return 'sha256:'+hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_text())
def origin(n,raw): return {'record':n,'end_line':n+1,'raw':raw}
def expected(key):
    if key=='all-bad': return [],[(1,['x','0','1.00'],'quantity'),(2,['y','2','1.005'],'price')],[],2
    if key=='empty': return [],[],[],0
    if key=='zero-price': return [['z',1,0,0]],[],[(1,['z','1','0.00'],'accepted',['z',1,0,0])],1
    if key=='quantity-upper': return [['u',100,100,10000]],[],[(1,['u','100','1.00'],'accepted',['u',100,100,10000])],1
    if key=='quantity-over': return [],[(1,['u','101','1.00'],'quantity')],[],1
    if key=='conflicting-id': return [ROWS[0]],[(2,['a','3','1.25'],'conflicting-id')],[(1,['a','2','1.25'],'accepted',ROWS[0])],2
    q=[] if key=='silent-skip' else [(4,['bad','nope','2.00'],'quantity')]
    l=[(1,['a','2','1.25'],'accepted',ROWS[0]),(2,['b','1','0.10'],'accepted',ROWS[1]),(3,['a','2','1.25'],'duplicate',ROWS[0])]
    return ROWS,q,l,4

def oracle(folder):
    obs=read(folder/'observation.json'); reports=[]
    assert len(obs['runs'])==13,'case count'
    for run in obs['runs']:
        key=run['id']; rows,q,typed,n=expected(key); previous=None
        assert read(folder/key/'input.json')==run['requests'],'input copy'
        for a,req in enumerate(run['requests'],1):
            case=folder/key; state=case/f'after-{a}'; command=read(case/f'attempt-{a}-command.json'); trace=read(case/f'attempt-{a}-trace.json')
            assert (case/f'attempt-{a}-source.csv').read_bytes()==req['csv'].encode(),'source bytes'
            for s in ('stdin','stdout','stderr'): assert sha(command[s].encode())==command[s+'_digest'],'command stream digest'
            assert json.loads(command['stdin'])==req and command['stderr']=='','command request/stderr'
            assert trace==[json.loads(line) for line in command['stdout'].splitlines()],'raw trace'
            failing=a==2 and key.endswith('after-success')
            exit_code=(2 if key.startswith('schema') else 3) if failing else 0
            assert command['exit_code']==exit_code==run['attempts'][a-1]['exit_code'],'exit code'
            terminal=[e for e in trace if e['event'] in ('published','refused','stage-failed')]
            outcome='refused' if exit_code==2 else 'stage-failed' if exit_code==3 else 'published'
            assert len(terminal)==1 and terminal[0]['event']==outcome,'terminal event'
            if failing:
                reason={'schema-refusal-after-success':'source-schema-mismatch','transform-failure-after-success':'injected-transform-stage','publish-failure-after-success':'injected-before-publish'}[key]
                assert terminal[0]['reason']==reason,'failure cause'
            assert trace[-1]=={'event':'cleanup','temporary_staging_removed':True},'cleanup event'
            assert not list((case/'publication').glob('.stage-*')) and not list((case/'publication').glob('.pointer-*')),'temporary cleanup'
            actual=list(csv.reader(io.StringIO((state/'output.csv').read_text(),newline='')))
            outrows=rows*2 if key=='append-rerun' and a==2 else rows
            fixed=[['id','quantity','price_cents','total_cents']]+[[str(v) for v in r] for r in outrows]
            assert actual==fixed,'hand rows differ'
            assert (state/'output.csv').read_text()==''.join(','.join(r)+'\n' for r in fixed),'canonical output bytes'
            assert read(state/'schema.json')==SCHEMA,'hand schema differ'
            quarantine=[origin(i,r)|{'reason':reason} for i,r,reason in q]
            assert read(state/'quarantine.json')==quarantine,'hand quarantine differ'
            lineages=[origin(i,r)|{'disposition':dis,'typed':t} for i,r,dis,t in typed]+[origin(i,r)|{'disposition':'quarantined'} for i,r,_ in q]
            lineages.sort(key=lambda r:r['record'])
            lineage=read(state/'lineage.json'); counts={'input':n,'accepted':len(rows),'duplicates':sum(t[2]=='duplicate' for t in typed),'quarantined':len(q)}
            assert lineage['counts']==counts and lineage['records']==lineages,'hand lineage/counts differ'
            successful=run['requests'][0] if failing else req
            assert lineage['input_digest']==sha(successful['csv'].encode()),'lineage input digest'
            assert lineage['producer_digest']==obs['source_bindings']['pipeline.py'],'lineage producer'
            assert lineage['mode']==successful['mode'] and lineage['bad_rows']==successful['bad_rows'],'lineage config'
            if not failing: assert len(list(csv.reader(io.StringIO(req['csv']))))-1==n,'physical source record count'
            manifest=read(state/'manifest.json')
            assert set(manifest)=={'output.csv','quarantine.json','schema.json','lineage.json'},'manifest set'
            for name,entry in manifest.items():
                raw=(state/name).read_bytes(); assert entry=={'digest':sha(raw),'size':len(raw)},'manifest binding'
            pointer=read(state/'current.json'); assert pointer=={'generation':hashlib.sha256((state/'manifest.json').read_bytes()).hexdigest()},'generation pointer'
            digestmap={p.name:sha(p.read_bytes()) for p in state.iterdir() if p.is_file()}
            unchanged=previous==digestmap if previous is not None else None
            if failing or (key=='replace-rerun' and a==2): assert unchanged,'previous state changed'
            reports.append({'id':key,'attempt':a,'outcome':outcome,'exit_code':exit_code,'rows':outrows,'schema':SCHEMA,'counts':counts,'unaccounted':n-sum(counts[k] for k in ('accepted','duplicates','quarantined')),'duplicate_output_ids':sorted({r[0] for r in outrows if sum(x[0]==r[0] for x in outrows)>1}),'unchanged_previous':unchanged,'output_digest':digestmap['output.csv'],'pointer_digest':digestmap['current.json'],'lineage':lineages,'quarantine':quarantine})
            previous=digestmap
        current=case/'publication'/'current.json'; pointer=read(current)
        for p in state.iterdir():
            location=current if p.name=='current.json' else case/'publication'/'generations'/pointer['generation']/p.name
            assert p.read_bytes()==location.read_bytes(),'live final publication differs'
    assert len(reports)==18,'attempt count'
    return {'passed':True,'cases':13,'attempts':18,'independence':'Fixed hand rows, schema, dispositions, counts; imports no producer or runner','reports':reports}

def check():
    folder=ROOT/read(ROOT/'current.json')['directory']; obs=read(folder/'observation.json')
    for name,d in obs['source_bindings'].items(): assert sha((ROOT/name).read_bytes())==d,'stale source '+name
    indexed=read(folder/'artifact-index.json')
    actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.name!='artifact-index.json'}
    assert actual==set(indexed),'artifact set'
    for name,e in indexed.items():
        p=folder/name; assert e=={'digest':sha(p.read_bytes()),'size':p.stat().st_size},'artifact digest '+name
    result=oracle(folder); assert result==read(folder/'oracle.json'),'saved oracle differs'
    print(json.dumps({'passed':True,'cases':13,'attempts':18,'read_only':True},ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--oracle'); args=p.parse_args()
    try:
        if args.oracle:
            assert re.fullmatch(r'(observations/[0-9TZ]+|oracle-negative-[a-zA-Z0-9_-]+)',args.oracle),'oracle path'
            print(json.dumps(oracle(ROOT/args.oracle),ensure_ascii=False))
        else: check()
    except (AssertionError,ValueError,KeyError,OSError) as exc:
        print(str(exc),file=sys.stderr); raise SystemExit(1)

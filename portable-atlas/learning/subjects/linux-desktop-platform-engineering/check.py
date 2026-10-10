import sys
sys.dont_write_bytecode=True
import argparse,ast,datetime,hashlib,itertools,json,re
from pathlib import Path
import model,oracle
ROOT=Path(__file__).resolve().parent
SHA=lambda b:hashlib.sha256(b).hexdigest()
def measurements(bootstrap=False):
    fixtures=json.loads((ROOT/'fixtures.json').read_text());cases=[]
    assert set(fixtures['entries'])==set(oracle.TOKENS)|set(oracle.REJECT) and fixtures['files']==oracle.FILES
    for case,selection in itertools.product(fixtures['entries'],fixtures['files']):
        d=model.experiment(case,selection);e=oracle.expected(case,selection);a=d['protected']
        assert {k:a[k] for k in e}==e,(case,selection,a,e)
        assert a['traceSha256']==model.digest(a['trace'])
        assert d['inputSha256']==model.digest({'entry':d['input']['entry'],'files':d['input']['files'],'launch':'argv-model'})
        if a['status']=='modeled':
            assert a['groups']['Desktop Entry']['X-Atlas-Note']=='preserved'
            assert [t['phase'] for t in a['trace']].count('string-unescape')==1
            assert [t['phase'] for t in a['trace']].count('token')==len(e['tokens'])
            assert a['trace'][-1]['argvModels']==e['argvModels']
        cases.append({'case':case,'selection':selection,'actual':d,'expected':e})
    hands=[('quoted','spaces',[['atlas-viewer','--label=two words','/synthetic/two words.txt','/synthetic/b.txt']]),('single','spaces',[['atlas-viewer','/synthetic/two words.txt'],['atlas-viewer','/synthetic/b.txt']]),('empty-arg','none',[['atlas-viewer','']]),('percent','percent-name',[['atlas-viewer','--progress=100%','/synthetic/%F.txt']])]
    for case,selection,argv in hands:assert model.experiment(case,selection)['protected']['argvModels']==argv
    reject_inputs=['', 'x'*2049,'Name=X\n[Desktop Entry]\nType=Application\nExec=atlas-viewer', '[Other]\nK=v\n[Desktop Entry]\nType=Application\nName=A\nExec=atlas-viewer', '[Desktop Entry]\n[Desktop Entry]', '[Desktop Entry]\nType=Application\nName=A\nTerminal=TRUE\nExec=atlas-viewer','[Desktop Entry]\nType=Application\nName=A\nExec=atlas-viewer %','[Desktop Entry]\nType=Application\nName=A\nExec=x=y','[Desktop Entry]\nType=Application\nName=A\nExec=atlas-viewer é','[Desktop Entry]\nType=Application\nName=A\nExec=atlas-viewer "cost$5"']
    boundary=[]
    for text in reject_inputs:
        result=model.compile_entry(text,[]);assert result['status']=='rejected';boundary.append({'input':{'entry':text,'files':[]},'actual':result})
    text=fixtures['entries']['quoted'];badfiles=[None,'x',['/real/file'],['/synthetic/'+('x'*130)],['/synthetic/a\n'],['/synthetic/a']*4,[True]]
    for files in badfiles:
        result=model.compile_entry(text,files);assert result['kind']=='bound';boundary.append({'input':{'entry':text,'files':files},'actual':result})
    for launch in ('shell','spawn','linux-gui'):
        result=model.compile_entry(text,[],launch);assert result['kind']=='policy';boundary.append({'input':{'entry':text,'files':[],'launch':launch},'actual':result})
    # Precisely test 2048-byte-character teaching bound using a comment prefix.
    tail='\n[Desktop Entry]\nType=Application\nName=A\nExec=atlas-viewer\n';exact='#'+'x'*(2048-len(tail)-1)+tail
    assert len(exact)==2048 and model.compile_entry(exact,[])['status']=='modeled'
    result=model.compile_entry(exact+'x',[]);assert result['kind']=='bound';boundary.append({'input':{'entry':exact+'x','files':[]},'actual':result})
    assert model.compile_entry(text,['/synthetic/'+'x'*(128-len('/synthetic/'))])['status']=='modeled'
    faults=[]
    for case,selection in [('quoted','spaces'),('single','spaces'),('empty-arg','none')]:
        d=model.experiment(case,selection);faulty=[d['bad']['argvModel']]
        assert faulty!=d['protected']['argvModels'];faults.append({'case':case,'selection':selection,'naive':faulty,'expected':d['protected']['argvModels']})
    expanded=model.experiment('plain','percent-name')['protected']['argvModels'];assert expanded==[['atlas-viewer','--read-only','/synthetic/%F.txt']]
    twice=[['atlas-viewer','--read-only','/synthetic/'+('/synthetic/%F.txt')+'.txt']];assert twice!=expanded
    faults.append({'fault':'recursive field expansion','faulty':twice,'expected':expanded})
    for row in boundary:row['inputSha256']=model.digest(row['input'])
    tree=ast.parse((ROOT/'model.py').read_text());names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}
    assert not names.intersection({'exec','eval','subprocess','os','popen','system'})
    for file in ('README.md','index.html'):
        content=(ROOT/file).read_text();assert all(url in content for url in model.SOURCES.values())
        assert '未教材' in content and 'argv' in content and 'Wayland' in content
    for match in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)',(ROOT/'README.md').read_text()):
        if not match.startswith('http'):
            if bootstrap and match in ('evidence/run.json','evidence/bindings.json','evidence/ui-qa.json','evidence/routing-smoke.json'):continue
            assert (ROOT/match).is_file(),match
    return {'caseCount':len(cases),'modeledCount':sum(x['expected']['status']=='modeled' for x in cases),'rejectedCount':sum(x['expected']['status']=='rejected' for x in cases),'handCount':len(hands),'boundaryRejectCount':len(reject_inputs)+len(badfiles)+3+1,'faultCount':len(faults),'boundary':boundary,'faults':faults,'cases':cases,'sources':model.SOURCES}
def bindings():return {str(p.relative_to(ROOT)):SHA(p.read_bytes()) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='bindings.json'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();m=measurements(a.record)
    if a.record:
        (ROOT/'evidence/run.json').write_text(json.dumps({'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':{'python':sys.version.split()[0],'platform':sys.platform},'measurements':m},ensure_ascii=False,indent=2)+'\n')
        (ROOT/'evidence/bindings.json').write_text(json.dumps({'sources':model.SOURCES,'files':bindings()},indent=2)+'\n')
    else:
        assert json.loads((ROOT/'evidence/run.json').read_text())['measurements']==m
        assert json.loads((ROOT/'evidence/bindings.json').read_text())=={'sources':model.SOURCES,'files':bindings()}
        qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['serverStopped'] and qa['tabClosed']
        for row in qa['cases']:
            d=model.experiment(row['case'],row['selection'],row['launch']);assert row['inputSha256']==d['inputSha256'] and row['traceSha256']==d['protected']['traceSha256']
            assert row['status']==d['protected']['status'] and row['argvModels']==d['protected']['argvModels']
        assert len(qa['cases'])==10
        assert json.loads((ROOT/'evidence/routing-smoke.json').read_text())['forwardAgentEval']=='not-run'
    print(json.dumps({k:v for k,v in m.items() if k not in ('cases','faults','boundary')},ensure_ascii=False))
if __name__=='__main__':main()

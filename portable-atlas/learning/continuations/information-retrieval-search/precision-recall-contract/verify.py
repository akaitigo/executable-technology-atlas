# SPDX-License-Identifier: Apache-2.0
import argparse,copy,hashlib,itertools,json,platform,re,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
import retrieval,oracle,route
HERE=Path(__file__).resolve().parent
SOURCE=['retrieval.py','oracle.py','verify.py','route.py','serve.py','fixture.json','hand-oracle.json','index.html','source.html','README.md','VERIFICATION.md','coverage.json','sources.json','skills/atlas-precision-recall-contract/SKILL.md']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate_quality(actual,expected):assert actual==expected

def execute():
 f=json.loads((HERE/'fixture.json').read_text());hand=json.loads((HERE/'hand-oracle.json').read_text());ids=hand['id_order'];assert [d['id'] for d in f['corpus']]==ids and f['relevant']==['d1','d2'];runs=[]
 for i,doc in enumerate(f['corpus']):assert oracle.words(doc['text'])==sorted(hand['document_tokens'][i])
 for case in f['cases']:
    scan=retrieval.scan(f['corpus'],case['query'],case['mode']);index=retrieval.indexed(f['corpus'],case['query'],case['mode']);h=hand['cases'][case['id']];expected=[id for id,bit in zip(ids,h['returned_bits']) if bit]
    assert scan['returned']==index['returned']==expected==oracle.retrieval_from_table(ids,hand['document_tokens'],case['query'],case['mode']);assert scan['terms']==index['terms']==oracle.words(case['query'])
    evaluations={}
    for labelmode,relevant,bits in [('specified',f['relevant'],hand['relevance_bits']),('empty-relevant',[],[0]*5),('missing-labels',None,None)]:
        q=retrieval.quality(ids,index['returned'],relevant);expected_quality=oracle.quality_from_bits(ids,h['returned_bits'],bits);validate_quality(q,expected_quality)
        if labelmode=='specified':
            assert [r['classification'] for r in q['rows']]==h['classes'] and list(q['counts'].values())==h['counts'] and q['precision']['value']==h['precision'] and q['recall']['value']==h['recall']
        evaluations[labelmode]=q
    runs.append(dict(id=case['id'],input=case,scan=scan,index=index,implementation_match=True,evaluations=evaluations))
 all_subsets=[]
 for bits in itertools.product([0,1],repeat=5):
    result=[id for id,hit in zip(ids,bits) if hit]
    for labelmode,relevant,relbits in [('specified',f['relevant'],hand['relevance_bits']),('empty-relevant',[],[0]*5),('missing-labels',None,None)]:
        actual=retrieval.quality(ids,result,relevant);expected=oracle.quality_from_bits(ids,bits,relbits);validate_quality(actual,expected);all_subsets.append(dict(returned_bits=list(bits),label_mode=labelmode,result=actual))
 invalid=[];corpus=f['corpus'];dup=copy.deepcopy(corpus);dup[1]['id']='d1';badtext=copy.deepcopy(corpus);badtext[0]['text']=None
 cases=[('corpus-type',None,'blue','AND'),('empty-corpus',[],'blue','AND'),('duplicate-id',dup,'blue','AND'),('document-text',badtext,'blue','AND'),('query-type',corpus,None,'AND'),('query-bool',corpus,True,'AND'),('query-too-long',corpus,'a'*129,'AND'),('non-ascii',corpus,'青','AND'),('unknown-mode',corpus,'blue','X')]
 for name,c,q,m in cases:
    try:retrieval.indexed(c,q,m)
    except ValueError as e:invalid.append(dict(id=name,input=dict(corpus=c,query=q,mode=m),status='EXPECTED_REFUSAL',error=str(e)))
    else:raise AssertionError(name)
 for name,result,relevant in [('retrieved-unknown',['d9'],['d1']),('retrieved-duplicate',['d1','d1'],['d1']),('retrieved-bool',[True],['d1']),('label-unknown',['d1'],['d9']),('label-duplicate',['d1'],['d1','d1']),('label-type',['d1'],'d1')]:
    try:retrieval.quality(ids,result,relevant)
    except ValueError as e:invalid.append(dict(id=name,input=dict(ids=ids,returned=result,relevant=relevant),status='EXPECTED_REFUSAL',error=str(e)))
    else:raise AssertionError(name)
 mutations=[];base=runs[1]['evaluations']['specified'];expected=oracle.quality_from_bits(ids,hand['cases']['or']['returned_bits'],hand['relevance_bits'])
 for name in ['precision-one','recall-half','wrong-FP','row-label','missing-denominator','undefined-as-one']:
    actual=copy.deepcopy(base);target=expected
    if name=='precision-one':actual['precision']['value']='1'
    elif name=='recall-half':actual['recall']['value']='1/2'
    elif name=='wrong-FP':actual['counts']['FP']=0
    elif name=='row-label':actual['rows'][2]['classification']='TP'
    elif name=='missing-denominator':actual['precision']['denominator']=None
    else:
        actual=copy.deepcopy(runs[2]['evaluations']['specified']);target=oracle.quality_from_bits(ids,[0]*5,hand['relevance_bits']);actual['precision']['value']='1';actual['precision']['status']='defined'
    try:validate_quality(actual,target)
    except AssertionError:mutations.append(dict(id=name,status='EXPECTED_REJECTION'))
    else:raise AssertionError(name)
 return dict(fixture=f,runs=runs,all_returned_subsets=all_subsets,invalid_inputs=invalid,evidence_mutations=mutations,fixed_evaluations=18,subset_evaluations=96,author_routing=dict(precision=route.route('precision'),ranking=route.route('ranking')),scope='synthetic labels; implementation correctness and quality are separate; no ranking/users/products/performance')
def docs():
 for f in ['README.md','skills/atlas-precision-recall-contract/SKILL.md']:
    for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
        if not link.startswith(('https:','#')):assert ((HERE/f).parent/link.split('#')[0].split('?')[0]).resolve().exists(),link
 c=json.loads((HERE/'coverage.json').read_text());ids={r['id'] for r in json.loads((HERE/'sources.json').read_text())};assert 2<=len(c['next_experiments'])<=4 and all(r['source'] in ids for r in c['areas']+c['next_experiments'])
def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--record');g.add_argument('--seal-record',action='store_true');args=p.parse_args();started=datetime.now(timezone.utc).isoformat();raw=execute();name=args.record or 'attempt-01';folder=HERE/'observations'/name
 if args.record:
    assert re.fullmatch(r'attempt-[0-9]+',name);folder.mkdir(exist_ok=False);raw['attempt']=dict(command='python3 verify.py --record '+name,started_at_utc=started,completed_at_utc=datetime.now(timezone.utc).isoformat(),exit_code=0,toolchain=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),input_sha256=sha(HERE/'fixture.json'),hand_oracle_sha256=sha(HERE/'hand-oracle.json'),executed_source_sha256={f:sha(HERE/f) for f in ['retrieval.py','oracle.py','verify.py']})
    (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
 else:
    old=json.loads((folder/'raw.json').read_text());assert {k:v for k,v in old.items() if k!='attempt'}==raw
 docs();sources={f:sha(HERE/f) for f in SOURCE};qa=json.loads((HERE/'observations/ui-qa.json').read_text())
 if qa['status']=='passed':
    for k,f in [('observed_ui_sha256','index.html'),('observed_sources_sha256','sources.json'),('observed_coverage_sha256','coverage.json'),('observed_raw_sha256','observations/attempt-01/raw.json')]:assert qa[k]==sha(HERE/f)
    ui=json.loads((HERE/'observations/ui-matrix.json').read_text());assert len(ui['rows'])==18 and len({(r['case'],r['label_mode']) for r in ui['rows']})==18
    state=json.loads((HERE/'observations/ui-state-transcript.json').read_text());assert state['prediction_changed']['prediction']=='separate' and state['prediction_changed']['comparison']==state['prediction_changed']['answer']==''
    for name in ['case_changed','labels_changed']:assert all(state[name][k]=='' for k in ['prediction','comparison','answer'])
    assert [r['input'] for r in state['invalid']]==['-1','5','']
    for r in state['invalid']:
        assert all(r[k]==state['before_invalid'][k] for k in ['prediction','comparison','answer','selected']) and r['error'].startswith('拒否')
    for r in ui['rows']:
        run=next(x for x in raw['runs'] if x['id']==r['case']);q=run['evaluations'][r['label_mode']];assert r['returned']==run['index']['returned'] and r['precision']==q['precision'] and r['recall']==q['recall'] and r['counts']==q['counts']
 if args.record or args.seal_record:
    files=[f for f in folder.iterdir() if f.name!='receipt.json']+[f for f in (HERE/'observations').iterdir() if f.is_file() and f.name!='read-only-proof.json'];receipt=dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py '+('--seal-record' if args.seal_record else '--record '+name),exit_code=0,sources=sources,artifacts={str(f.relative_to(HERE)):sha(f) for f in files},checks=dict(scan_index_and_literal='passed',fixed_evaluations=18,subset_evaluations=96,expected_refusals=len(raw['invalid_inputs']),evidence_mutation_rejections=6,actual_iab=qa['status'],skill='author smoke; no independent AgentEval'))
    (folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 else:
    receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==sources
    for f,h in receipt['artifacts'].items():assert sha(HERE/f)==h,f
 print(json.dumps(dict(status='passed',retrieval_cases=6,fixed_evaluations=18,all_subset_evaluations=96,expected_refusals=len(raw['invalid_inputs']),evidence_mutations=6,record=args.record,seal_record=args.seal_record)))
if __name__=='__main__':main()

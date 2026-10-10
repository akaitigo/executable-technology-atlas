# SPDX-License-Identifier: Apache-2.0
"""Independent retrieval and literal-fact oracle. Read-only unless --record is explicit."""
import argparse
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import re
import sys
sys.dont_write_bytecode=True
import pipeline
import route

HERE=Path(__file__).resolve().parent
SOURCES=['pipeline.py','verify.py','route.py','serve.py','corpus.json','fixtures.json','oracle-facts.json',
         'README.md','index.html','coverage.json','sources.json','VERIFICATION.md','skills/atlas-generative-ai-rag/SKILL.md']


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def split_words(text):
    # Character translation and split, independent of production regex tokenizer.
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(c if c in alphabet else ' ' for c in text.lower()).split()


def retrieval_oracle(corpus,fixture):
    query=set(split_words(fixture['query']))
    candidates=[]
    for doc in corpus:
        count=sum(word in query for word in split_words(doc['text']))
        candidates.append((doc['id'],count))
    # Repeated maximum selection rather than the production sorted ranking.
    ordered=[]
    while candidates:
        maximum=max(score for _,score in candidates)
        name=min(name for name,score in candidates if score==maximum)
        ordered.append((name,maximum));candidates.remove((name,maximum))
    chosen=[name for name,score in ordered if score>0][:fixture['top_k']]
    return ordered,chosen


def context_oracle(corpus,fixture,chosen,facts):
    lookup={doc['id']:doc for doc in corpus};space=fixture['max_chars'];selected=[]
    for name in chosen:
        # Golden authored reference inventory is separate from production kind filter.
        if name in facts and len(lookup[name]['text'])<=space:
            selected.append(name);space-=len(lookup[name]['text'])
    return selected


def check(corpus,fixture,policy,facts):
    actual=pipeline.run(corpus,fixture,policy)
    ordered,chosen=retrieval_oracle(corpus,fixture)
    assert [(r['id'],r['score']) for r in actual['ranked']]==ordered
    assert [r['id'] for r in actual['retrieved']]==chosen
    context=context_oracle(corpus,fixture,chosen,facts)
    assert [d['id'] for d in actual['context']]==context
    corpus_ids={doc['id'] for doc in corpus};lookup={doc['id']:doc for doc in corpus}
    expected=[]
    for claim,row in zip(fixture['claims'],actual['checks']):
        exists=claim['citation'] in corpus_ids
        supported=(claim['citation'] in context and claim['text']==claim['quote']
                   and claim['text'] in facts.get(claim['citation'],[]))
        accepted=supported if policy=='strict' else exists
        assert row['citation_exists']==exists and row['supported']==supported and row['accepted']==accepted
        assert row['in_context']==(claim['citation'] in context)
        if row['source_span']:
            begin,end=row['source_span']
            assert lookup[claim['citation']]['text'][begin:end]==claim['quote']
        expected.append(dict(citation_exists=exists,literal_supported=supported,accepted=accepted))
    assert len(actual['checks'])==len(fixture['claims'])
    status='abstained' if not expected else ('accepted' if all(row['accepted'] for row in expected) else 'rejected')
    assert actual['status']==status
    assert [t['stage'] for t in actual['trace']]==['query','retrieve','context','authored-answer','binding','result']
    assert actual['trace'][-1]['status']==status
    return actual,dict(retrieved=chosen,context=context,claims=expected,status=status)


def execute():
    corpus=json.loads((HERE/'corpus.json').read_text());fixtures=json.loads((HERE/'fixtures.json').read_text())
    facts=json.loads((HERE/'oracle-facts.json').read_text())
    assert len(corpus)==4 and set(facts)=={'archive-hours','garden-hours','archive-room'}
    for doc in corpus:
        for fact in facts.get(doc['id'],[]):assert fact in doc['text']
    runs=[]
    for fixture in fixtures:
        outcomes={};oracles={}
        for policy in ('strict','citation-only'):
            outcomes[policy],oracles[policy]=check(corpus,fixture,policy,facts)
        runs.append(dict(id=fixture['id'],input=fixture,policies=outcomes,independent_oracle=oracles))
    by={r['id']:r for r in runs}
    assert by['normal']['policies']['strict']['status']=='accepted'
    assert by['garden-normal']['policies']['strict']['status']=='accepted'
    assert by['abstain-no-context']['policies']['strict']['status']=='abstained'
    for name in set(by)-{'normal','garden-normal','abstain-no-context','missing-citation'}:
        assert by[name]['policies']['strict']['status']=='rejected', name
        assert by[name]['policies']['citation-only']['status']=='accepted', name
    assert by['missing-citation']['policies']['citation-only']['status']=='rejected'
    assert by['untrusted-instruction']['policies']['strict']['checks'][0]['quote_is_source_sentence']
    assert not by['untrusted-instruction']['policies']['strict']['checks'][0]['reference_allowed']
    assert by['two-claims-partial']['policies']['strict']['trace'][-1]['supported_claims']==1
    for citation,sentences in facts.items():
        for sentence in sentences:
            fixture=dict(query='archive garden bags entry',top_k=8,max_chars=2048,claims=[dict(text=sentence,citation=citation,quote=sentence)])
            actual,_=check(corpus,fixture,'strict',facts)
            assert actual['status']=='accepted'
    rng=random.Random(20261005);vocabulary=['archive','garden','opens','closes','seats','bags','east','comet','09','00']
    for _ in range(120):
        fixture=dict(id='variation',query=' '.join(rng.sample(vocabulary,rng.randint(1,4))),top_k=rng.randint(0,4),
                     max_chars=rng.randint(0,400),claims=fixtures[0]['claims'])
        for policy in ('strict','citation-only'):check(corpus,fixture,policy,facts)
    invalid=[]
    for name,change in [('empty-query',dict(query='')),('no-ascii-tokens',dict(query='???')),('negative-k',dict(top_k=-1)),
                        ('bool-k',dict(top_k=True)),('too-large-k',dict(top_k=9)),('negative-budget',dict(max_chars=-1)),
                        ('bool-budget',dict(max_chars=True)),('too-large-budget',dict(max_chars=2049)),
                        ('claim-shape',dict(claims=[{'text':'x'}])),('too-many-claims',dict(claims=fixtures[0]['claims']*9))]:
        fixture=dict(fixtures[0],**change)
        try:pipeline.run(corpus,fixture)
        except ValueError as e:invalid.append(dict(id=name,input=fixture,error=str(e)))
        else:raise AssertionError(name)
    corpus_invalid=[]
    altered=[('empty',[]),('duplicate',corpus+[corpus[0]]),('kind',[dict(corpus[0],kind='unknown')]),
             ('missing-text',[{'id':'x','kind':'reference'}])]
    for name,documents in altered:
        try:pipeline.run(documents,fixtures[0])
        except ValueError as e:corpus_invalid.append(dict(id=name,error=str(e)))
        else:raise AssertionError(name)
    try:pipeline.run(corpus,fixtures[0],'unknown')
    except ValueError as e:option_error=str(e)
    else:raise AssertionError('policy')
    return dict(pipeline_version=pipeline.VERSION,corpus=corpus,corpus_sha256=digest(HERE/'corpus.json'),
                input_sha256=digest(HERE/'fixtures.json'),oracle_inventory_sha256=digest(HERE/'oracle-facts.json'),
                runs=runs,invalid_inputs=invalid,invalid_corpus=corpus_invalid,invalid_policy=option_error,randomized_queries=120,
                oracle_scope='independent character-scan retrieval, greedy context budget and golden literal fact inventory; no semantic truth oracle',
                generation='none: fixed author fixtures',author_routing_smoke={'citation':route.route('citation'),'llm-generation':route.route('llm-generation')})


def docs_check(record):
    planned={HERE/'observations/raw.json',HERE/'observations/receipt.json'}
    for filename in ['README.md','skills/atlas-generative-ai-rag/SKILL.md']:
        for link in re.findall(r'\]\(([^)]+)\)',(HERE/filename).read_text()):
            if not link.startswith(('https:','#')):
                target=((HERE/filename).parent/link.split('#')[0]).resolve()
                assert target.exists() or (record and target in planned),link
    text=(HERE/'README.md').read_text()
    assert all(word in text for word in ['前提','主要概念','実務判断','限界','原典','未教材'])
    coverage=json.loads((HERE/'coverage.json').read_text());sources=json.loads((HERE/'sources.json').read_text())
    ids={s['id'] for s in sources}
    assert 2<=len(coverage['next_experiments'])<=4
    for area in coverage['areas']+coverage['next_experiments']:assert area['source'] in ids and area['question']
    assert all(s in (HERE/'index.html').read_text() for s in ['coverage.json','sources.json','README.md'])
    assert route.route('citation')['status']=='supported' and route.route('llm-generation')['status']=='unsupported'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true');args=parser.parse_args()
    data=execute();docs_check(args.record);sources={f:digest(HERE/f) for f in SOURCES};folder=HERE/'observations'
    if args.record:
        (folder/'raw.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        names=['observations/raw.json','observations/ui-qa.json']
        for optional in ['ui-matrix.json','preview-http.log']:
            if (folder/optional).exists():names.append('observations/'+optional)
        receipt=dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py --record',
                     environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),
                     corpus_sha256=data['corpus_sha256'],input_sha256=data['input_sha256'],sources=sources,
                     artifacts={f:digest(HERE/f) for f in names},checks=dict(runtime_oracle='passed',roadmap_links_binding='passed',
                     author_routing_smoke='passed; not independent AgentEval',actual_iab_qa=json.loads((folder/'ui-qa.json').read_text())['status']))
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    else:
        receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==sources,'source changed; explicit --record required'
        assert receipt['corpus_sha256']==data['corpus_sha256'] and receipt['input_sha256']==data['input_sha256']
        for f,h in receipt['artifacts'].items():assert digest(HERE/f)==h,f
        assert data==json.loads((folder/'raw.json').read_text()),'runtime replay mismatch'
        qa=json.loads((folder/'ui-qa.json').read_text())
        if qa.get('observed_raw_sha256'):assert qa['observed_raw_sha256']==digest(folder/'raw.json'),'UI raw binding changed'
    print(json.dumps(dict(status='passed',record=args.record,runs=len(data['runs']),randomized_queries=120,
                         invalid_inputs=len(data['invalid_inputs']),invalid_corpus=len(data['invalid_corpus']))))

if __name__=='__main__':main()

"""Independent hand ranges/span/character inventory; no producer imports."""
import copy,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def validate(case,v):
    hand=json.loads((ROOT/'hand-oracle.json').read_text());f=json.loads((ROOT/'fixtures.json').read_text())[case];corpus=json.loads((ROOT/'corpus.json').read_text());e=json.loads((ROOT/'evidence.json').read_text());h=hand['cases'][case];r=v['result'];assert v['case']==case and v['fixture']==f and v['corpus']==corpus and v['evidence']==e
    assert {n:len(s) for n,s in corpus.items()}==hand['source_lengths']
    assert {k:e[k] for k in ('doc','start','end','literal')}==hand['evidence'] and corpus[e['doc']][16:36]==e['literal']
    for n,digest in v['source_binding'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==digest
    assert set(v['source_binding'])=={'pipeline.py','runner.py','corpus.json','evidence.json','fixtures.json','hand-oracle.json'}
    assert v['utc'].endswith('+00:00') and v['runtime']['python'] and r['status']==h['status']
    if case=='invalid-overlap':assert r==dict(status=h['status'],reason=h['reason'],pipeline_started=False);return
    assert r['pipeline_started'] is True;ranges=hand['ranges'][str(f['overlap'])];by_id={c['id']:c for c in r['chunks']};assert len(by_id)==sum(map(len,ranges.values()))
    for doc,pairs in ranges.items():
        assert [[c['start'],c['end']] for c in r['chunks'] if c['doc']==doc]==pairs
        for start,end in pairs:
            c=by_id[doc+':'+str(start)];assert c['text']==corpus[doc][start:end] and c['characters']==end-start
            complete=doc=='garden' and start<=16 and end>=36
            assert c['complete_span']==complete
            # A query hit is only the exact four-character Gate at offsets16..20.
            expected_score=1 if f['query']=='Gate' and doc=='garden' and start<=16 and end>=20 else 0
            assert c['score']==expected_score
    hits=['garden:'+str(n) for n in h['hits']];full=['garden:'+str(n) for n in h['complete']];included=['garden:'+str(n) for n in h['included']]
    assert r['ranked_ids']==hits and r['complete_span_chunk_ids']==full and r['included_ids']==included
    assert r['retrieved_complete_span_ids']==[n for n in hits if n in full] and r['retrieval_hit']==bool(hits) and r['included_context_support']==h['support']
    assert (r['context_characters'],r['context_unique_source_characters'],r['context_duplicate_source_characters'])==(h['used'],h['unique'],h['duplicate'])
    # Independent per-source offset counting and prefix capacity table.
    covered={};used=0;expected_trace=[];expected_ids=[]
    for id in hits:
        c=by_id[id];cost=c['end']-c['start'];before=used;fits=cost<=f['budget']-used
        if fits:
            used+=cost;expected_ids.append(id)
            for offset in range(c['start'],c['end']):covered[(c['doc'],offset)]=covered.get((c['doc'],offset),0)+1
        expected_trace.append(dict(chunk=id,characters=cost,before=before,after=used,decision='included' if fits else 'budget-excluded'))
    assert expected_ids==included and expected_trace==r['budget_trace'] and len(covered)==h['unique']
    assert sum(count-1 for count in covered.values())==h['duplicate'] and used<=f['budget']
    bad=r['bad_judgment'];assert bad['enabled']==(f['policy']=='hit-only') and bad['claims_supported']==(bool(hits) if bad['enabled'] else h['support']) and bad['rule_failed']==(case=='bad-retrieval-hit-only')
def verify():
    paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths
    for p in paths:
        raw=json.loads(p.read_text());assert set(raw)==set(json.loads((ROOT/'fixtures.json').read_text()))
        for n,v in raw.items():validate(n,v)
    rejected=[]
    def reject(label,case,edit):
        v=copy.deepcopy(raw[case]);edit(v)
        try:validate(case,v)
        except (AssertionError,KeyError):rejected.append(label);return
        raise AssertionError('mutation escaped '+label)
    reject('broken span treated as full','boundary-broken',lambda v:v['result'].update(complete_span_chunk_ids=['garden:0']))
    reject('excluded evidence accepted','overlap-budget-excluded',lambda v:v['result'].update(included_context_support=True))
    reject('duplicate budget hidden','heavy-overlap-excluded',lambda v:v['result'].update(context_duplicate_source_characters=0))
    reject('original offset shifted','overlap-retained',lambda v:v['result']['chunks'][2].update(start=1))
    reject('bad hit-only judgment declared safe','bad-retrieval-hit-only',lambda v:v['result']['bad_judgment'].update(rule_failed=False))
    return dict(valid_strict_cases=6,supported_contexts=2,unsupported_contexts=4,bad_judgments=1,expected_input_refusals=1,recorded_runs=len(paths),independent_hand_ranges_span_budget=True,mutations_rejected=rejected)
if __name__=='__main__':print(json.dumps(verify(),indent=2))

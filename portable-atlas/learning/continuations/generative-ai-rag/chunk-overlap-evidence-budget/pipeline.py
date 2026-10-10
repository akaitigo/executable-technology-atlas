"""Authored literal/offset/character contract, no models/tokenizers/embeddings."""
def run(f,corpus,evidence):
    size=f['size'];overlap=f['overlap'];budget=f['budget']
    if not type(overlap) is int or not 0<=overlap<size:return dict(status='INPUT_REJECTED',reason='OVERLAP_MUST_BE_SMALLER_THAN_SIZE',pipeline_started=False)
    chunks=[];trace=[]
    for doc,text in sorted(corpus.items()):
        start=0
        while start<len(text):
            end=min(start+size,len(text));literal=text[start:end];complete=doc==evidence['doc'] and start<=evidence['start'] and end>=evidence['end'] and literal[evidence['start']-start:evidence['end']-start]==evidence['literal']
            chunk=dict(id=doc+':'+str(start),doc=doc,start=start,end=end,text=literal,characters=end-start,score=literal.count(f['query']),complete_span=complete);chunks.append(chunk)
            if end==len(text):break
            start+=size-overlap
    ranked=sorted([c for c in chunks if c['score']>0],key=lambda c:(-c['score'],c['doc'],c['start']))
    included=[];used=0
    for chunk in ranked:
        fits=used+chunk['characters']<=budget;before=used
        if fits:included.append(chunk);used+=chunk['characters']
        trace.append(dict(chunk=chunk['id'],characters=chunk['characters'],before=before,after=used,decision='included' if fits else 'budget-excluded'))
    offsets={(c['doc'],i) for c in included for i in range(c['start'],c['end'])};support=any(c['complete_span'] for c in included);bad=f['policy']=='hit-only';claims=bool(ranked) if bad else support
    return dict(status='BAD_ACCEPTED' if bad and claims else 'SUPPORTED' if support else 'UNSUPPORTED',pipeline_started=True,chunks=chunks,ranked_ids=[c['id'] for c in ranked],retrieval_hit=bool(ranked),complete_span_chunk_ids=[c['id'] for c in chunks if c['complete_span']],retrieved_complete_span_ids=[c['id'] for c in ranked if c['complete_span']],included_ids=[c['id'] for c in included],included_context_support=support,context_characters=used,context_unique_source_characters=len(offsets),context_duplicate_source_characters=used-len(offsets),budget_trace=trace,bad_judgment=dict(enabled=bad,claims_supported=claims,rule_failed=bad and claims and not support))

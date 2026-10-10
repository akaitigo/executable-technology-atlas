# SPDX-License-Identifier: Apache-2.0
"""Lexical retrieval -> bounded context -> authored fixture citation checks. No generator."""
import re

VERSION='lexical-grounding-1'


def tokens(text):
    return re.findall(r'[a-z0-9]+',text.lower())


def validate_corpus(corpus):
    if not isinstance(corpus,list) or not 1<=len(corpus)<=16:
        raise ValueError('corpus requires 1..16 documents')
    ids=set()
    for doc in corpus:
        if not isinstance(doc,dict) or not isinstance(doc.get('id'),str) or not doc['id'] or doc['id'] in ids:
            raise ValueError('document ids must be nonempty and unique')
        if doc.get('kind') not in ('reference','instruction-fixture'):
            raise ValueError('unsupported document kind')
        if not isinstance(doc.get('text'),str) or not 1<=len(doc['text'])<=4000:
            raise ValueError('document text length must be 1..4000')
        ids.add(doc['id'])


def run(corpus,fixture,policy='strict'):
    validate_corpus(corpus)
    if policy not in ('strict','citation-only'):
        raise ValueError('unsupported checking policy')
    if not isinstance(fixture,dict):
        raise ValueError('fixture must be an object')
    query=fixture.get('query');k=fixture.get('top_k');budget=fixture.get('max_chars');claims=fixture.get('claims')
    if not isinstance(query,str) or not 1<=len(query)<=200 or not tokens(query):
        raise ValueError('query requires 1..200 characters and ASCII lexical tokens')
    if type(k) is not int or not 0<=k<=8:
        raise ValueError('top_k must be integer 0..8')
    if type(budget) is not int or not 0<=budget<=2048:
        raise ValueError('max_chars must be integer 0..2048')
    if not isinstance(claims,list) or len(claims)>8:
        raise ValueError('authored fixture requires 0..8 claims')
    for claim in claims:
        if not isinstance(claim,dict) or any(not isinstance(claim.get(key),str) or not 1<=len(claim[key])<=300 for key in ('text','citation','quote')):
            raise ValueError('claim text/citation/quote must be nonempty strings up to 300 characters')
    words=set(tokens(query))
    ranked=[]
    for doc in corpus:
        terms=tokens(doc['text'])
        matched={word:terms.count(word) for word in sorted(words) if word in terms}
        ranked.append(dict(id=doc['id'],score=sum(matched.values()),matches=matched,kind=doc['kind']))
    ranked.sort(key=lambda row:(-row['score'],row['id']))
    retrieved=[r for r in ranked if r['score']>0][:k]
    lookup={doc['id']:doc for doc in corpus}
    context=[];omitted=[];used=0
    for candidate in retrieved:
        doc=lookup[candidate['id']]
        if doc['kind']!='reference':
            omitted.append(dict(id=doc['id'],reason='instruction-fixture is data without reference authority'))
            continue
        # Budget is Python character count of whole document texts, not LLM tokens.
        if used+len(doc['text'])>budget:
            omitted.append(dict(id=doc['id'],reason='whole document exceeds remaining character budget'))
            continue
        context.append(dict(id=doc['id'],text=doc['text'],characters=len(doc['text'])))
        used+=len(doc['text'])
    trace=[dict(stage='query',tokens=sorted(words)),dict(stage='retrieve',ranked=ranked,selected=retrieved),
           dict(stage='context',documents=context,omitted=omitted,characters=used,budget=budget),
           dict(stage='authored-answer',claims=claims,origin='fixed author fixture; no model generation')]
    context_ids={d['id'] for d in context}
    checks=[]
    for claim in claims:
        doc=lookup.get(claim['citation'])
        exists=doc is not None
        in_context=claim['citation'] in context_ids
        allowed=exists and doc['kind']=='reference'
        # Exact atomic-sentence support only. No paraphrase, entailment or truth judgment.
        sentences=[s.strip() for s in re.findall(r'[^.]+\.',doc['text'])] if exists else []
        quote_exists=exists and claim['quote'] in sentences
        answer_matches=claim['text']==claim['quote']
        supported=bool(exists and in_context and allowed and quote_exists and answer_matches)
        accepted=supported if policy=='strict' else exists
        offset=doc['text'].find(claim['quote']) if quote_exists else -1
        checks.append(dict(claim=claim,citation_exists=exists,in_context=in_context,reference_allowed=bool(allowed),
                           quote_is_source_sentence=bool(quote_exists),answer_matches_quote=answer_matches,
                           supported=supported,accepted=accepted,
                           source_span=[offset,offset+len(claim['quote'])] if offset>=0 else None))
    trace.append(dict(stage='binding',checks=checks,policy=policy))
    status='abstained' if not claims else ('accepted' if all(c['accepted'] for c in checks) else 'rejected')
    trace.append(dict(stage='result',status=status,accepted_claims=sum(c['accepted'] for c in checks),
                      supported_claims=sum(c['supported'] for c in checks),total_claims=len(claims)))
    return dict(status=status,ranked=ranked,retrieved=retrieved,context=context,omitted=omitted,checks=checks,trace=trace,
                scope='Literal sentence/context binding only; no generated answer, semantic entailment or prompt-injection detector')

# SPDX-License-Identifier: Apache-2.0
import re
from fractions import Fraction
def validate(corpus,query,mode):
 if not isinstance(corpus,list) or not 1<=len(corpus)<=32:raise ValueError('corpus list length1..32 required')
 if mode not in ['AND','OR','ALL_DIAGNOSTIC']:raise ValueError('unknown retrieval mode')
 if not isinstance(query,str) or len(query)>128 or not query.isascii():raise ValueError('ASCII query string length0..128 required')
 ids=[]
 for doc in corpus:
    if not isinstance(doc,dict) or set(doc)!={'id','text'} or not isinstance(doc['id'],str) or not re.fullmatch(r'd[0-9]+',doc['id']):raise ValueError('document exact id/text fields required')
    if not isinstance(doc['text'],str) or not doc['text'].isascii() or len(doc['text'])>256:raise ValueError('ASCII document text required')
    ids.append(doc['id'])
 if len(set(ids))!=len(ids):raise ValueError('unique IDs required')
def tokenize(text):return sorted(set(re.findall('[a-z0-9]+',text.lower())))
def scan(corpus,query,mode):
 validate(corpus,query,mode);terms=tokenize(query);returned=[];rows=[]
 for doc in corpus:
    tokens=tokenize(doc['text']);flags=[t in tokens for t in terms];hit=mode=='ALL_DIAGNOSTIC' or bool(terms) and (all(flags) if mode=='AND' else any(flags));rows.append(dict(id=doc['id'],tokens=tokens,term_matches=flags,returned=hit))
    if hit:returned.append(doc['id'])
 return dict(returned=sorted(returned),terms=terms,rows=rows)
def indexed(corpus,query,mode):
 validate(corpus,query,mode);postings={}
 for doc in corpus:
    for term in tokenize(doc['text']):postings.setdefault(term,set()).add(doc['id'])
 terms=tokenize(query);steps=[]
 if mode=='ALL_DIAGNOSTIC':result={d['id'] for d in corpus}
 elif not terms:result=set()
 else:
    result=postings.get(terms[0],set()).copy();steps.append(dict(term=terms[0],posting=sorted(result),accumulated=sorted(result)))
    for term in terms[1:]:
        posting=postings.get(term,set());result=result&posting if mode=='AND' else result|posting;steps.append(dict(term=term,posting=sorted(posting),accumulated=sorted(result)))
 return dict(returned=sorted(result),terms=terms,postings={t:sorted(v) for t,v in sorted(postings.items())},steps=steps)
def quality(ids,returned,relevant):
 if not isinstance(returned,list) or any(not isinstance(x,str) for x in returned) or len(set(returned))!=len(returned) or not set(returned)<=set(ids):raise ValueError('unique retrieved corpus IDs required')
 if relevant is not None and (not isinstance(relevant,list) or any(not isinstance(x,str) for x in relevant) or len(set(relevant))!=len(relevant) or not set(relevant)<=set(ids)):raise ValueError('labels must be None or unique corpus IDs')
 ret=set(returned);rows=[]
 if relevant is None:
    for id in ids:rows.append(dict(id=id,returned=id in ret,relevant=None,classification='UNJUDGED'))
    return dict(rows=rows,counts=dict(TP=None,FP=None,FN=None,TN=None),precision=dict(value=None,numerator=None,denominator=len(ret),status='unjudged'),recall=dict(value=None,numerator=None,denominator=None,status='unjudged'),label_status='missing')
 rel=set(relevant);tp=ret&rel;fp=ret-rel;fn=rel-ret;tn=set(ids)-ret-rel;counts=dict(TP=len(tp),FP=len(fp),FN=len(fn),TN=len(tn))
 for id in ids:rows.append(dict(id=id,returned=id in ret,relevant=id in rel,classification='TP' if id in tp else 'FP' if id in fp else 'FN' if id in fn else 'TN'))
 def metric(den):return dict(value=str(Fraction(len(tp),den)) if den else None,numerator=len(tp),denominator=den,status='defined' if den else 'undefined-zero-denominator')
 return dict(rows=rows,counts=counts,precision=metric(len(ret)),recall=metric(len(rel)),label_status='judged')

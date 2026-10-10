# SPDX-License-Identifier: Apache-2.0
"""ID-wise fixed truth table, not producer set operations. Imports no retriever."""
from fractions import Fraction
def quality_from_bits(ids,returned_bits,relevance_bits):
 rows=[];counts={'TP':0,'FP':0,'FN':0,'TN':0};retrieved_count=0;relevant_count=0
 for i,id in enumerate(ids):
    hit=bool(returned_bits[i]);retrieved_count+=int(hit)
    if relevance_bits is None:rel=None;label='UNJUDGED'
    else:
        rel=bool(relevance_bits[i]);relevant_count+=int(rel)
        # Literal four-cell contingency lookup indexed by relevant,returned.
        label=[['TN','FP'],['FN','TP']][int(rel)][int(hit)];counts[label]+=1
    rows.append(dict(id=id,returned=hit,relevant=rel,classification=label))
 if relevance_bits is None:return dict(rows=rows,counts={k:None for k in counts},precision=dict(value=None,numerator=None,denominator=retrieved_count,status='unjudged'),recall=dict(value=None,numerator=None,denominator=None,status='unjudged'),label_status='missing')
 def ratio(d):return dict(value=str(Fraction(counts['TP'],d)) if d else None,numerator=counts['TP'],denominator=d,status='defined' if d else 'undefined-zero-denominator')
 return dict(rows=rows,counts=counts,precision=ratio(retrieved_count),recall=ratio(relevant_count),label_status='judged')
def words(text):
 result=[];word=''
 for c in text.lower()+' ':
    if 'a'<=c<='z' or '0'<=c<='9':word+=c
    elif word:
        if word not in result:result.append(word)
        word=''
 return sorted(result)
def retrieval_from_table(ids,token_rows,query,mode):
 terms=words(query);bits=[]
 for tokens in token_rows:
    hits=sum(1 for term in terms if term in tokens)
    bits.append(int(mode=='ALL_DIAGNOSTIC' or bool(terms) and (hits==len(terms) if mode=='AND' else hits>0)))
 return [id for id,bit in zip(ids,bits) if bit]

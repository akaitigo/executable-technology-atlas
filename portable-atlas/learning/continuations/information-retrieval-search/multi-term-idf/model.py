"""Atlas: bounded multi-term score calculation, not a search engine."""
import math,re

class InputError(ValueError):
 def __init__(self,code,details=None):super().__init__(code);self.code=code;self.details=details or {}
def need(ok,code):
 if not ok:raise InputError(code)
PARAMETERS={'k1':1,'b':0,'idf':'ln(N/df)','query_duplicates':'deduplicate','query_order':'lexicographic','unknown_term':'reject whole query','candidate':'any query term','tie':'document ID ascending'}
def validate(data):
 need(type(data) is dict and set(data)=={'title','schema','documents','parameters','queries'},'input_keys')
 need(type(data['schema']) is int and data['schema']==1,'schema')
 params=data['parameters'];need(type(params) is dict and params==PARAMETERS and type(params.get('k1')) is int and type(params.get('b')) is int,'fixed_parameters')
 docs=data['documents'];need(type(docs) is list and len(docs)==4,'document_count')
 seen=set();parsed=[]
 for d in docs:
  need(type(d) is dict and set(d)=={'id','text'},'document_keys');need(type(d['id']) is str and d['id'] in ['d1','d2','d3','d4'],'document_id');need(d['id'] not in seen,'duplicate_document_id');seen.add(d['id'])
  text=d['text'];need(type(text) is str and len(text)<=64 and re.fullmatch(r'[a-z]+(?: [a-z]+)*',text) is not None,'document_tokens')
  tokens=text.split(' ');need(len(tokens)==4 and all(len(t)<=16 for t in tokens),'fixed_document_length');need(all(tokens.count(t)<=1 for t in ['alpha','beta']),'fixed_frequency')
  parsed.append({'id':d['id'],'tokens':tokens})
 return parsed
def ranks(rows,key):
 ordered=sorted((r for r in rows if r['matched']),key=lambda r:(-r[key],r['id']));groups=[]
 for r in ordered:
  if groups and groups[-1][0]==r[key]:groups[-1][1].append(r['id'])
  else:groups.append([r[key],[r['id']]])
 return [r['id'] for r in ordered],[ids for _,ids in groups if len(ids)>1]
def calculate(data,request_id,query):
 docs=validate(data);need(type(request_id) is str and re.fullmatch(r'[a-z-]{1,32}',request_id) is not None,'request_id')
 need(type(query) is str and len(query)<=64 and re.fullmatch(r'[a-z]+(?: [a-z]+){0,2}',query) is not None,'query_tokens')
 original=query.split(' ');need(all(len(t)<=16 for t in original),'query_token_length');terms=sorted(set(original));N=len(docs);df={t:sum(t in d['tokens'] for d in docs) for t in terms};missing=[t for t in terms if df[t]==0]
 if missing:raise InputError('unknown_query_term',{'missing_terms':missing})
 need(all(t in ['alpha','beta'] for t in terms),'query_outside_lesson')
 idfs={t:math.log(N/df[t]) for t in terms};rows=[]
 for d in sorted(docs,key=lambda d:d['id']):
  contributions=[]
  for t in terms:
   positions=[i for i,word in enumerate(d['tokens']) if word==t];tf=len(positions)
   factor=(2*tf)/(1+tf) if tf else 0.0
   contributions.append({'term':t,'positions':positions,'tf':tf,'df':df[t],'idf':idfs[t],'tf_factor':factor,'weighted_contribution':idfs[t]*factor,'unit_contribution':factor,'nonmatch_short_circuit':tf==0})
  rows.append({'id':d['id'],'tokens':d['tokens'],'length':len(d['tokens']),'contributions':contributions,'matched':any(c['tf']>0 for c in contributions),'weighted_score':sum(c['weighted_contribution'] for c in contributions),'unit_score':sum(c['unit_contribution'] for c in contributions)})
 weighted,weighted_ties=ranks(rows,'weighted_score');unit,unit_ties=ranks(rows,'unit_score')
 for r in rows:r.update(weighted_rank=weighted.index(r['id'])+1 if r['matched'] else None,unit_rank=unit.index(r['id'])+1 if r['matched'] else None)
 return {'request_id':request_id,'query':query,'status':'calculated','query_tokens':original,'canonical_terms':terms,'removed_duplicates':len(original)-len(terms),'N':N,'total_tokens':sum(len(d['tokens']) for d in docs),'avgdl':sum(len(d['tokens']) for d in docs)/N,'k1':1,'b':0,'idf_variant':'ln(N/df)','df':df,'idf':idfs,'matches':[r['id'] for r in rows if r['matched']],'weighted_order':weighted,'weighted_ties':weighted_ties,'unit_order':unit,'unit_ties':unit_ties,'rows':rows,'search_engine_executed':False,'user_relevance_evaluated':False}

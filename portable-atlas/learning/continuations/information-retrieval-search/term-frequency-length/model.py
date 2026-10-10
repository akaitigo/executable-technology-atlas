"""Atlas: finite term-frequency/document-length calculation; not a search product."""
import copy,math,re

MODES=[
 {'id':'raw-tfidf','formula':'tf * ln(N/df)','k1':None,'b':None},
 {'id':'bm25-b0','formula':'IIR equation 86, single query term','k1':1,'b':'0'},
 {'id':'bm25-bhalf','formula':'IIR equation 86, single query term','k1':1,'b':'1/2'},
 {'id':'bm25-b1','formula':'IIR equation 86, single query term','k1':1,'b':'1'}]
B={'bm25-b0':0.0,'bm25-bhalf':0.5,'bm25-b1':1.0}

def require(value,label):
 if not value:raise ValueError(label)

def validate(data):
 require(type(data) is dict and set(data)=={'title','schema','query','documents','modes'},'input_keys')
 require(type(data['schema']) is int and data['schema']==1,'schema')
 require(type(data['title']) is str and 1<=len(data['title'])<=80,'title')
 require(type(data['query']) is str and re.fullmatch('[a-z]{1,16}',data['query']),'single_query_token')
 docs=data['documents'];require(type(docs) is list and len(docs)==4,'four_documents')
 for doc in docs:
  require(type(doc) is dict and set(doc)=={'id','text'},'document_keys')
  require(type(doc['id']) is str and doc['id'] in ['d1','d2','d3','d4'],'document_id')
  text=doc['text'];require(type(text) is str and len(text)<=128 and re.fullmatch('(?:[a-z]+(?: [a-z]+)*)?',text) is not None,'document_tokens')
  require(len(text.split())<=8 and all(len(t)<=16 for t in text.split()),'token_bound')
 require(len({x['id'] for x in docs})==4,'duplicate_document_id')
 modes=data['modes'];require(type(modes) is list and len(modes)==4,'four_modes')
 for actual,expected in zip(modes,MODES):
  require(type(actual) is dict and set(actual)==set(expected),'mode_keys')
  require(actual==expected and (actual['k1'] is None or type(actual['k1']) is int),'fixed_mode_contract')
 require(sum(len(x['text'].split()) for x in docs)>0,'empty_corpus')
 require(any(data['query'] in x['text'].split() for x in docs),'query_not_in_corpus')
 return data

def calculate(data,mode_id):
 validate(data);require(type(mode_id) is str and mode_id in [x['id'] for x in MODES],'unknown_mode')
 query=data['query'];tokens={x['id']:x['text'].split() for x in data['documents']}
 N=len(tokens);df=sum(query in ts for ts in tokens.values());total=sum(len(ts) for ts in tokens.values());avg=total/N;idf=math.log(N/df)
 rows=[]
 for doc_id,ts in sorted(tokens.items()):
  positions=[i for i,t in enumerate(ts) if t==query];tf=len(positions);length=len(ts);matched=tf>0
  numerator=denominator=None
  if not matched:coefficient=0.0
  elif mode_id=='raw-tfidf':numerator=float(tf);denominator=1.0;coefficient=numerator/denominator
  else:
   k1=1.0;b=B[mode_id];numerator=(k1+1)*tf;denominator=k1*(1-b+b*length/avg)+tf;coefficient=numerator/denominator
  rows.append({'id':doc_id,'tokens':ts,'length':length,'term_frequency':tf,'positions':positions,'matched':matched,'numerator':numerator,'denominator':denominator,'coefficient':coefficient,'score':idf*coefficient,'rank':None,'nonmatch_short_circuit':not matched})
 ranked=sorted([row for row in rows if row['matched']],key=lambda row:(-row['score'],row['id']))
 for rank,row in enumerate(ranked,1):row['rank']=rank
 ties=[]
 for row in ranked:
  ids=[x['id'] for x in ranked if x['score']==row['score']]
  if len(ids)>1 and ids not in ties:ties.append(ids)
 return {'mode_id':mode_id,'query':query,'N':N,'df':df,'total_tokens':total,'avgdl':avg,'idf_variant':'ln(N/df)','idf':idf,'k1':None if mode_id=='raw-tfidf' else 1,'b':None if mode_id=='raw-tfidf' else B[mode_id],'match_ids':sorted(x['id'] for x in ranked),'nonmatch_ids':sorted(x['id'] for x in rows if not x['matched']),'matched_order':[x['id'] for x in ranked],'tie_groups':ties,'rows':rows,'scope':'finite Python score calculation; no real search engine; usefulness unjudged'}

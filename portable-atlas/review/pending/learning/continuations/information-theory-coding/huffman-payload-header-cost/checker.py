"""Independent length-assignment oracle and table decoder; never imports producer."""
import copy,itertools,json,math,sys
from fractions import Fraction as F
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,digest,run,snapshot
ABC=list('ABCD');HAND=json.loads((ROOT/'hand-oracle.json').read_text())
SHAPES=[v for v in itertools.product(range(1,4),repeat=4) if sum(2**(3-n) for n in v)==8]
assert len(SHAPES)==13 and {tuple(sorted(v)) for v in SHAPES}=={(2,2,2,2),(1,2,3,3)}
def independent_book(lengths):
 # Enumerate lexicographic binary words and discard descendants of assigned words.
 available=[''.join(v) for v in itertools.product('01',repeat=3)];book={}
 for c in sorted(ABC,key=lambda c:(lengths[c],c)):
  word=available[0][:lengths[c]];book[c]=word;available=[w for w in available if not w.startswith(word)]
 assert not available;return {c:book[c] for c in ABC}
def independent_decode(book,bits,n):
 out=[];position=0
 while position<len(bits):
  matches=[(c,w) for c,w in book.items() if bits[position:position+len(w)]==w];assert len(matches)==1
  c,w=matches[0];out.append(c);position+=len(w)
 assert position==len(bits) and len(out)==n;return ''.join(out)
def inspect(r,x):
 assert r['status']=='calculated';s=r['summary'];assert s['input']==x
 w=x['weights'];m=x['message'];n=len(m);lens=s['lengths'];book=s['codebook'];v=tuple(lens[c] for c in ABC);assert v in SHAPES and book==independent_book(lens)
 assert all(not b.startswith(a) for c,a in book.items() for d,b in book.items() if c!=d)
 cost=sum(w[i]*v[i] for i in range(4));assert cost==min(sum(w[i]*candidate[i] for i in range(4)) for candidate in SHAPES)
 assert s['probabilities']==[str(F(a,sum(w))) for a in w] and s['weighted_mean_length']==str(F(cost,sum(w))) and s['fixed_mean_length']=='2'
 assert math.isclose(s['entropy_bits_per_symbol_approx'],sum(float(F(a,sum(w)))*math.log2(sum(w)/a) for a in w),abs_tol=1e-12)
 # Trace oracle uses a sorted forest rather than a heap; verify every actual merge.
 forest=[(a,c) for a,c in zip(w,ABC)];depth={c:0 for c in ABC}
 assert len(s['merge_trace'])==3
 for event in s['merge_trace']:
  forest.sort(key=lambda item:(item[0],min(ABC.index(c) for c in item[1])));a,b=forest[:2];forest=forest[2:]
  assert event==dict(left=a[1],right=b[1],left_weight=a[0],right_weight=b[0],merged_weight=a[0]+b[0])
  for c in a[1]+b[1]:depth[c]+=1
  forest.append((a[0]+b[0],a[1]+b[1]))
 assert depth==lens and s['symbol_counts']=={c:m.count(c) for c in ABC} and s['message_length']==n
 hcost=sum(m.count(c)*lens[c] for c in ABC);fcost=2*n
 assert s['actual_payload_mean']==(str(F(hcost,n)) if n else None)
 for kind,headers,expectedcost,expectedbook in [('huffman',16,hcost,book),('fixed',8,fcost,dict(zip(ABC,['00','01','10','11'])))]:
  a=s[kind];assert a['header_bits']==headers and a['payload_bits']==expectedcost and a['total_bits']==headers+expectedcost
  assert a['payload']==''.join(expectedbook[c] for c in m) and a['packet']==a['header']+a['payload'] and len(a['packet'])==a['total_bits']
  assert len(a['header'])==headers and int(a['header'][:8],2)==n
  if kind=='huffman':assert [int(a['header'][8+2*i:10+2*i],2)+1 for i in range(4)]==list(v)
  assert a['receiver_inputs']==dict(codebook=expectedbook,bitstream=a['payload'],count=n)
  decoded=independent_decode(expectedbook,a['payload'],n);assert a['decoded']==decoded==m and a['harness_match'] is True
 diff=16+hcost-8-fcost;assert s['category']==('saved' if diff<0 else 'equal' if diff==0 else 'overhead') and s['total_difference_bits']==diff
 assert s['payload_saves']==s['wrong_payload_only_claim']==(hcost<fcost) and s['total_saves']==(diff<0) and s['wrong_claim_detected']==(hcost<fcost and diff>=0)
 assert r['context']==dict(synthetic_bit_protocol=True,original_used_only_by_harness=True,standard_format=False,speed_measured=False,capacity_achieved=False,physical_channel_measured=False)
def handcheck(r,name):
 h=HAND['cases'][name];s=r['summary'];assert s['codebook']==h['codebook'] and s['weighted_mean_length']==h['weighted_mean_length'] and s['entropy_bits_per_symbol_approx']==h['entropy']
 for key,path in [('payload_bits',('huffman','payload_bits')),('fixed_payload_bits',('fixed','payload_bits')),('huffman_total_bits',('huffman','total_bits')),('fixed_total_bits',('fixed','total_bits'))]:assert s[path[0]][path[1]]==h[key]
 assert s['category']==h['category']
def main():
 before=snapshot();valid=[];rows=json.loads((ROOT/'expected-table.json').read_text())['rows']
 for row in rows:
  p=run(row['input_json']);r=p['result'];assert p['stderr']=='' and json.loads(p['stdout'])==r
  if row['expected']['status']=='calculated':assert p['exit']==0;inspect(r,json.loads(row['input_json']));handcheck(r,row['id']);valid.append(r)
  else:assert p['exit']==2 and r==dict(status='input_refusal',code=row['expected']['code'],summary=None)
 mutations=['ignore-header','fixed-header-zero','prefix-collision','wrong-mean','wrong-entropy','wrong-tie','wrong-count','copy-original-decoder','wrong-payload','empty-mean-zero','payload-is-total','capacity-claim'];rejected=[]
 for name in mutations:
  r=copy.deepcopy(valid[5] if name=='empty-mean-zero' else valid[0]);s=r['summary']
  if name=='ignore-header':s['category']='saved';s['total_saves']=True
  elif name=='fixed-header-zero':s['fixed']['header_bits']=0
  elif name=='prefix-collision':s['codebook']['C']='01'
  elif name=='wrong-mean':s['weighted_mean_length']='2'
  elif name=='wrong-entropy':s['entropy_bits_per_symbol_approx']=2
  elif name=='wrong-tie':s['merge_trace'][1]['left']='CD'
  elif name=='wrong-count':s['huffman']['receiver_inputs']['count']=7
  elif name=='copy-original-decoder':s['huffman']['receiver_inputs']['original']=s['input']['message']
  elif name=='wrong-payload':s['huffman']['payload']='0'
  elif name=='empty-mean-zero':s['actual_payload_mean']='0'
  elif name=='payload-is-total':s['huffman']['total_bits']=14
  else:r['context']['capacity_achieved']=True
  try:inspect(r,s['input'])
  except (AssertionError,KeyError,ValueError,TypeError,IndexError):rejected.append(name)
  else:raise AssertionError('survived '+name)
 if (ROOT/'observation-data.js').exists():
  raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.HUFFMAN_OBSERVATION=').strip().removesuffix(';'));folder=ROOT/'observations'/raw['run_id'];assert raw==json.loads((folder/'raw.json').read_text()) and raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
  for n in ['calculate.py','hand-oracle.json','contracts.json','expected-table.json']:assert digest(folder/n)==digest(ROOT/n)
  for row in raw['rows']:
   assert json.loads(row['run']['stdout'])==row['run']['result']
   if row['expected']['status']=='calculated':inspect(row['run']['result'],json.loads(row['input_json']));handcheck(row['run']['result'],row['id'])
   else:assert row['run']['result']==dict(status='input_refusal',code=row['expected']['code'],summary=None) and row['run']['exit']==2
 assert before==snapshot();print(json.dumps(dict(hand_cases=6,refused=6,full_four_leaf_assignments=13,mutants_rejected=rejected,unit_sha_mtime_unchanged=True)));return 0
if __name__=='__main__':sys.exit(main())

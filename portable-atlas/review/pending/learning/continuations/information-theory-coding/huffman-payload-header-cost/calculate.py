"""Four-symbol bit protocol. Receiver has no source message or weights."""
import heapq,json,math,sys
from fractions import Fraction
sys.dont_write_bytecode=True
ABC=list('ABCD');FORMAT='canonical-lengths-2bit-plus-u8-count-v1'
class Refusal(ValueError):pass
def validate(x):
 if type(x) is not dict or set(x)!=set(['alphabet','weights','message','header_format']):raise Refusal('shape')
 if x['alphabet']!=ABC:raise Refusal('alphabet')
 w=x['weights']
 if type(w) is not list or len(w)!=4 or any(type(v) is not int or not 1<=v<=16 for v in w):raise Refusal('weights')
 m=x['message']
 if type(m) is not str or len(m)>255 or any(c not in ABC for c in m):raise Refusal('message')
 if x['header_format']!=FORMAT:raise Refusal('header')
def canonical(lengths):
 if set(lengths)!=set(ABC) or any(type(v) is not int or not 1<=v<=3 for v in lengths.values()):raise Refusal('length-header')
 if sum(Fraction(1,2**v) for v in lengths.values())!=1:raise Refusal('kraft')
 ordered=sorted(ABC,key=lambda c:(lengths[c],ABC.index(c)));book={};number=0;previous=lengths[ordered[0]]
 for i,c in enumerate(ordered):
  length=lengths[c]
  if i:number=(number+1)<<(length-previous)
  book[c]=format(number,'0'+str(length)+'b');previous=length
 return {c:book[c] for c in ABC}
def construct(weights):
 heap=[(w,i,i,c) for i,(w,c) in enumerate(zip(weights,ABC))];heapq.heapify(heap);trace=[];serial=4
 def leaves(n):return n if type(n) is str else leaves(n[0])+leaves(n[1])
 while len(heap)>1:
  a,b=heapq.heappop(heap),heapq.heappop(heap);node=(a[3],b[3]);trace.append({'left':leaves(a[3]),'right':leaves(b[3]),'left_weight':a[0],'right_weight':b[0],'merged_weight':a[0]+b[0]});heapq.heappush(heap,(a[0]+b[0],min(a[1],b[1]),serial,node));serial+=1
 lengths={}
 def walk(node,depth):
  if type(node) is str:lengths[node]=depth
  else:walk(node[0],depth+1);walk(node[1],depth+1)
 walk(heap[0][3],0);return {c:lengths[c] for c in ABC},trace

def decode(codebook,bitstream,count):
 """Only receiver dictionary, payload and explicit length; original is absent."""
 if type(count) is not int or not 0<=count<=255:raise Refusal('count')
 if type(codebook) is not dict or set(codebook)!=set(ABC):raise Refusal('book')
 words=list(codebook.values())
 if any(type(w) is not str or not w or set(w)-set('01') for w in words) or len(set(words))!=4:raise Refusal('book')
 if any(a!=b and b.startswith(a) for a in words for b in words):raise Refusal('prefix')
 if type(bitstream) is not str or set(bitstream)-set('01'):raise Refusal('bits')
 reverse={v:k for k,v in codebook.items()};out=[];prefix=''
 for bit in bitstream:
  if len(out)==count:raise Refusal('excess-bits')
  prefix+=bit
  if prefix in reverse:out.append(reverse[prefix]);prefix=''
  elif not any(w.startswith(prefix) for w in words):raise Refusal('invalid-prefix')
 if prefix or len(out)!=count:raise Refusal('truncated')
 return ''.join(out)
def receive_huffman(packet):
 if type(packet) is not str or len(packet)<16 or set(packet)-set('01'):raise Refusal('packet')
 count=int(packet[:8],2);lengths={c:int(packet[8+2*i:10+2*i],2)+1 for i,c in enumerate(ABC)};book=canonical(lengths);bits=packet[16:]
 return dict(codebook=book,bitstream=bits,count=count,decoded=decode(book,bits,count))
def receive_fixed(packet):
 if type(packet) is not str or len(packet)<8 or set(packet)-set('01'):raise Refusal('packet')
 count=int(packet[:8],2);book=dict(zip(ABC,['00','01','10','11']));bits=packet[8:]
 return dict(codebook=book,bitstream=bits,count=count,decoded=decode(book,bits,count))
def calculate(x):
 validate(x);weights=x['weights'];m=x['message'];n=len(m);lengths,trace=construct(weights);book=canonical(lengths);fixed=dict(zip(ABC,['00','01','10','11']));p=[Fraction(w,sum(weights)) for w in weights];mean=sum(p[i]*lengths[c] for i,c in enumerate(ABC));header=format(n,'08b')+''.join(format(lengths[c]-1,'02b') for c in ABC);fh=format(n,'08b');payload=''.join(book[c] for c in m);fp=''.join(fixed[c] for c in m);packet=header+payload;fpacket=fh+fp;hr=receive_huffman(packet);fr=receive_fixed(fpacket);ht=len(packet);ft=len(fpacket)
 def report(h,p,packet,receiver):return dict(header=h,payload=p,packet=packet,header_bits=len(h),payload_bits=len(p),total_bits=len(packet),receiver_inputs={k:receiver[k] for k in ['codebook','bitstream','count']},decoded=receiver['decoded'],harness_match=receiver['decoded']==m)
 s=dict(input=x,probabilities=[str(v) for v in p],entropy_bits_per_symbol_approx=-sum(float(v)*math.log2(float(v)) for v in p),weighted_mean_length=str(mean),fixed_mean_length='2',lengths=lengths,codebook=book,merge_trace=trace,symbol_counts={c:m.count(c) for c in ABC},message_length=n,actual_payload_mean=str(Fraction(len(payload),n)) if n else None,huffman=report(header,payload,packet,hr),fixed=report(fh,fp,fpacket,fr),payload_saves=len(payload)<len(fp),total_saves=ht<ft,total_difference_bits=ht-ft,category='saved' if ht<ft else 'equal' if ht==ft else 'overhead',wrong_payload_only_claim=len(payload)<len(fp),wrong_claim_detected=len(payload)<len(fp) and ht>=ft)
 return {'status':'calculated','summary':s,'context':{'synthetic_bit_protocol':True,'original_used_only_by_harness':True,'standard_format':False,'speed_measured':False,'capacity_achieved':False,'physical_channel_measured':False}}
def main():
 try:
  def pairs(items):
   d={}
   for k,v in items:
    if k in d:raise Refusal('json')
    d[k]=v
   return d
  x=json.loads(sys.stdin.read(),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Refusal('json')));r=calculate(x);exit=0
 except (json.JSONDecodeError,Refusal) as e:r={'status':'input_refusal','code':str(e) if isinstance(e,Refusal) else 'json','summary':None};exit=2
 print(json.dumps(r,ensure_ascii=False,allow_nan=False));return exit
if __name__=='__main__':sys.exit(main())

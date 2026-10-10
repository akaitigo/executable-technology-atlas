#!/usr/bin/env python3
import hashlib,json,pathlib
from fractions import Fraction
ROOT=pathlib.Path(__file__).resolve().parent
# producer非import。独立event ID集合と手書き分数・bool・拒否表。
SPECS={'normal':(0,[0,1],[0,1],False,False,None),'spike':(0,[4,1],[2,5],False,True,None),'sustained':(0,[2,1],[2,1],True,True,None),'recovered':(0,[0,1],[2,1],False,False,None),'boundaries':(0,[10,1],[10,1],True,True,None),'short-empty':(2,None,[0,1],None,None,'empty-window:short'),'all-outside':(2,None,None,None,None,'empty-window:long,short'),'empty':(2,None,None,None,None,'empty-window:long,short'),'unknown-status':(2,None,None,None,None,'unknown-status:timeout'),'duplicate-id':(2,None,None,None,None,'duplicate-id:0'),'boolean-tick':(2,None,None,None,None,'invalid-tick:bool')}
ALL=list(range(100));SHORT=list(range(90,100))
IDS={'normal':ALL,'spike':ALL,'sustained':ALL,'recovered':ALL,'boundaries':[89,90,99,100],'short-empty':list(range(90)),'all-outside':list(range(100,200)),'empty':[],'unknown-status':ALL,'duplicate-id':ALL+[0],'boolean-tick':[0]}
BAD={'normal':[],'spike':[96,97,98,99],'sustained':list(range(18))+[90,91],'recovered':list(range(20)),'boundaries':[89,90,99,100],'short-empty':[],'all-outside':[],'empty':[]}
WIN={'normal':(ALL,SHORT),'spike':(ALL,SHORT),'sustained':(ALL,SHORT),'recovered':(ALL,SHORT),'boundaries':([89,90,99],[90,99]),'short-empty':(list(range(90)),[]),'all-outside':([],[]),'empty':([],[])}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pair(f):return [f.numerator,f.denominator]
def check(run):
 d=json.loads((run/'result.json').read_text());assert json.loads((run/'stdout.json').read_text())==d
 for n,h in json.loads((run/'artifacts.json').read_text()).items():assert (run/n).stat().st_size==h['bytes'] and digest(run/n)==h['sha256'],n
 for n,h in d['sourceHashes'].items():assert digest(ROOT/n)==h,n
 assert digest(run/'worker.py')==digest(ROOT/'worker.py') and digest(run/'expected.json')==digest(ROOT/'expected.json')
 prior=json.loads((run/'expected.json').read_text());assert prior['policy']=={'slo':[9,10],'threshold':[2,1],'long':[0,100],'short':[90,100],'comparison':'>=','join':'AND'}
 assert prior['cases']=={n:dict(exit=s[0],short=s[1],long=s[2],**{'and':s[3],'shortOnly':s[4]},**({'reason':s[5]} if s[5] else {})) for n,s in SPECS.items()},'prior independent table'
 assert [c['id'] for c in d['cases']]==list(SPECS)
 for c in d['cases']:
  n=c['id'];o=c['observation'];code,short,long,decision,bug,reason=SPECS[n];folder=run/n;events=json.loads((folder/'input.json').read_text())
  assert c['argv']==['python3','-B','worker.py',n+'/input.json'] and digest(folder/'input.json')==c['inputSha256']
  assert c['stdout']==(folder/'stdout.json').read_text() and json.loads(c['stdout'])==o and c['stderr']==(folder/'stderr.txt').read_text()==''
  assert c['exitCode']==code and o['reason']==reason,'exit/refusal literal';assert o['input']==events and [e['id'] for e in events]==IDS[n],'input ID literal'
  for e in events:
   assert set(e)==set(['id','tick','status']) and type(e['id']) is int
   expectedTick=True if n=='boolean-tick' else e['id'];assert type(e['tick']) is type(expectedTick) and e['tick']==expectedTick,'input tick literal'
   status='timeout' if n=='unknown-status' and e['id']==0 else ('bad' if e['id'] in BAD.get(n,[]) else 'good');assert e['status']==status,'input status literal'
  assert o['slo']==[9,10] and o['threshold']==[2,1]
  assert o['and'] is decision and o['shortOnly'] is bug,'AND vs short-only literal'
  if n not in WIN:assert o['windows'] is None,'invalid input not evaluated';continue
  for name,expectedIds,burn in [('long',WIN[n][0],long),('short',WIN[n][1],short)]:
   w=o['windows'][name];failed=sorted(set(expectedIds)&set(BAD[n]));assert w['range']==([0,100] if name=='long' else [90,100])
   assert w['eventIds']==expectedIds and w['failedIds']==failed,'independent ID sets';assert w['denominator']==len(expectedIds) and w['failures']==len(failed),'integer counts'
   assert w['burn']==burn,'handwritten burn fraction'
   if burn is None:assert w['errorRate'] is None and w['overThreshold'] is None and w['burnText']=='未定義'
   else:
    f=Fraction(*burn);assert w['burnText']==str(f) and w['overThreshold'] is (f>=2);assert w['errorRate']==pair(Fraction(len(failed),len(expectedIds)));assert f*Fraction(1,10)*len(expectedIds)==len(failed),'integer/fraction invariant'
 return d
if __name__=='__main__':check(ROOT/(ROOT/'CURRENT').read_text().strip());print('PASS 11 cases; independent event ID sets, literal Fraction burn and AND/refusal')

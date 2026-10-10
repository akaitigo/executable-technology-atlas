import sys
sys.dont_write_bytecode=True
import hashlib
# Independent RFC2104 SHA256 ipad/opad construction; no admission imports.
KEY=b'atomic-admission-public-fixture-key-v1'
HAND_COUNTS={'same':[1,2,2,2,2,1,1,1],'different':[2]*8,'preseen':[0]*8,'invalid':[0]*8,'mixed':[1]*8,'payload':[1,2,2,2,2,1,1,1],'boundary':[1,2,2,2,2,1,1,1]}
ORDERS=[['Ac','Aw','Bc','Bw'],['Ac','Bc','Aw','Bw'],['Ac','Bc','Bw','Aw'],['Bc','Ac','Aw','Bw'],['Bc','Ac','Bw','Aw'],['Bc','Bw','Ac','Aw'],['A','B'],['B','A']]
def mac(r):
 key=KEY.ljust(64,b'\0');data=r['id'].encode('ascii')+bytes([0])+r['payload'].encode('utf-8')
 inner=hashlib.sha256(bytes(v^0x36 for v in key)+data).digest()
 return hashlib.sha256(bytes(v^0x5c for v in key)+inner).hexdigest()==r['tag']
def expected(f,index):
 events=ORDERS[index];requests=dict(zip('AB',f['requests']));good={n:mac(r) for n,r in requests.items()}
 accepted={}
 # Position relation, not producer's event loop: accepted writes before each check.
 for n in sorted('AB',key=lambda n:events.index(n+'c' if index<6 else n)):
  c=n+'c' if index<6 else n
  prior=[requests[k]['id'] for k,v in accepted.items() if v and events.index(k+'w' if index<6 else k)<events.index(c)]
  accepted[n]=good[n] and requests[n]['id'] not in f['seen']+prior
 return dict(accepted_count=sum(accepted.values()),seen=sorted(set(f['seen']+[requests[n]['id'] for n in 'AB' if accepted[n]])),accepted=accepted,authenticated=good)

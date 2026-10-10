"""Independent literal bytes and actual HTTP decompression. No producer import."""
import json,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TABLE=json.loads((ROOT/'oracle.json').read_text());FIXTURE=json.loads((ROOT/'fixture.json').read_text())
def validate_wire(w,encoding,failure=False):
 assert w['headers']['cache-control']=='no-store' and w['headers']['x-request-id']==w['request_id'] and w['path'].endswith('?request='+w['request_id'])
 assert len(bytes.fromhex(w['body_hex']))==w['body_bytes']==int(w['headers']['content-length'])
 if failure:assert w['http_status']==500 and w['body_hex']==b'injected HTTP failure'.hex() and w['decoded_hex'] is None;return
 assert w['http_status']==200 and w['body_hex']==TABLE['plain_hex' if encoding=='plain' else 'gzip_hex'] and w['body_bytes']==(3 if encoding=='plain' else 23)
 body=bytes.fromhex(w['body_hex']);decoded=gzip.decompress(body) if encoding=='gzip' else body
 assert decoded.hex()==w['decoded_hex']==TABLE['decoded_hex'] and len(decoded)==w['decoded_bytes']==3
 assert w['headers'].get('content-encoding')==('gzip' if encoding=='gzip' else None)
def validate(raw):
 assert raw['fixture']==FIXTURE and len(raw['cases'])==16
 ids=[]
 for c,x in zip(FIXTURE['cases'],raw['cases']):
  r,w=x['result'],x['wire'];e=TABLE['expected'][c['id']];assert r['case']==c['id'];ids.append(c['id'])
  if e['status']=='INPUT_REFUSED':assert r['status']==e['status'] and r['reason']==e['reason'] and w is None and r['measurement'] is None and r['accepted'] is None;continue
  assert r['input']==c;validate_wire(w,c['encoding'],c['variant']=='http-failure')
  if c['variant']=='timing-missing':assert r['status']=='BROWSER_REQUIRED' and r['accepted'] is None and r['measurement'] is None;continue
  assert r['status']==e['status'] and r['reason']==e['reason'] and r['used']==e['used'] and r['accepted'] is e['accepted']
  assert r['measurement']==(None if e['encoded'] is None else dict(encoded=e['encoded'],decoded=e['decoded']))
 assert len({x['wire']['request_id'] for x in raw['cases'] if x['wire']})==11
 return dict(http_cases=11,input_refused=5,browser_required=1,shared_producer=False,wire_total_bytes=False)

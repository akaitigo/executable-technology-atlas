import json,hashlib,datetime,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parent
ORDER=['person','email','category','agree','send']
NAMES=['名前','メール','種別','同意','送信']
LITERAL=[('fixed-1000',1000,False,False,True),('fixed-320',320,True,False,True),('fluid-1000',1000,False,True,False),('fluid-320',320,False,True,False)]
def read(n):return json.loads((P/n).read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def instant(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
def image_size(f):
 b=f.read_bytes();assert b[:2]==b'\xff\xd8' and len(b)>5000;i=2
 while i<len(b):
  assert b[i]==255;m=b[i+1];n=struct.unpack('>H',b[i+2:i+4])[0]
  if m in [192,193,194,195]:h,w=struct.unpack('>HH',b[i+5:i+9]);return w,h
  i+=2+n
 raise AssertionError('no JPEG size')
def blank(o):assert o['status']=='未実行' and o['raw'] is None and o['answer']=='' and not o['answer_open'] and not o['answer_visible']
def measured(r,source_root=P):
 assert len(r['cases'])==4 and r['zoom']=='UNMEASURED' and 'not browser zoom' in r['viewport_method']
 assert instant(r['completed'])>=instant(r['started'])
 for n,h in r['source_sha256'].items():assert sha(source_root/n)==h,n
 for (cid,width,overflow,outline,covered),o in zip(LITERAL,r['cases']):
  assert o['id']==cid and o['requestedViewport']==dict(width=width,height=800)
  m=o['initial'];assert m['condition']==cid and m['viewport']['clientWidth']==m['viewport']['innerWidth']==width and m['viewport']['clientHeight']==800
  assert (m['document']['scrollWidth']>width)==overflow and m['document']['scrollHeight']>800
  assert [x['id'] for x in m['controls']]==ORDER and all(x['display']!='none' for x in m['controls'])
  assert len(o['tabs'])==5 and o['submitted']=='合成送信回数: 1'
  for i,t in enumerate(o['tabs']):
   m=t['measurement'];a=m['active'];v=m['viewport'];assert t['expected_id']==a['id']==ORDER[i] and m['condition']==cid
   assert v['clientWidth']==width and v['clientHeight']==800 and m['zoom']=='UNMEASURED'
   assert a['focusVisible'] and a['outlineWidth']==('3px' if outline else '0px') and a['outlineStyle']==('solid' if outline else 'none')
   assert [k['from'] for k in m['keyEvents']]==['start']+ORDER[:i] and all(k['trusted'] and k['key']=='Tab' and not k['shift'] for k in m['keyEvents'])
   assert [f['id'] for f in m['focusEvents']]==ORDER[:i+1] and all(f['trusted'] for f in m['focusEvents'])
   focus=t['nativeAX'].split('The focused UI element is ')[-1];assert NAMES[i] in focus and 'AXWebArea' not in focus
   assert image_size(P/t['capture'])==(width,800)
   if outline:assert a['rect']['left']>=0 and a['rect']['right']<=width
   for e in m['controls']:
    er=e['rect'];assert e['visibleViewport']==(er['left']>=0 and er['right']<=width and er['top']>=0 and er['bottom']<=800)
  m=o['tabs'][-1]['measurement'];a=m['active'];c=m['cover'];ar=a['rect'];cr=c['rect']
  area=max(0,min(ar['right'],cr['right'])-max(ar['left'],cr['left']))*max(0,min(ar['bottom'],cr['bottom'])-max(ar['top'],cr['top']))
  assert c['activeOverlapArea']==area and (area>0)==covered
  if covered:assert c['display']=='flex' and area==ar['width']*ar['height'] and not a['centerHitIsActive']
  else:assert c['display']=='none' and a['centerHit']==dict(id='send',tag='BUTTON') and a['centerHitIsActive']
  if cid=='fixed-1000':assert a['centerHit']==dict(id='cover',tag='SPAN')
  if cid=='fixed-320':assert a['centerHit'] is None and ar['left']<0
def ui(r,b):
 assert len(b['cases'])==4
 for o,u in zip(r['cases'],b['cases']):
  assert o['id']==u['id'] and u['raw']==dict(observation=o,source_sha256=r['source_sha256']) and u['status']=='SAVED_OBSERVATION' and u['answer_open'] and u['answer_visible']
  m=o['initial'];a=o['tabs'][-1]['measurement']['active'];c=o['tabs'][-1]['measurement']['cover']
  for s in ['条件='+o['id'],'実viewport='+str(m['viewport']['clientWidth'])+'×800','document scrollWidth='+str(m['document']['scrollWidth']),'横overflow='+str(m['document']['scrollWidth']>m['viewport']['clientWidth']).lower(),'Tab='+'→'.join(ORDER),'send outline='+a['outlineWidth']+' '+a['outlineStyle'],'send centerHit='+json.dumps(a['centerHit'],ensure_ascii=False,separators=(',',':')),'cover overlap='+str(c['activeOverlapArea']),'幅の流動化単独がfocus/遮蔽を修復した証拠ではない','viewport縮小はBrowser zoomではない','保存済み観測の比較','予想overflow='+json.dumps(u['inputs'][0],ensure_ascii=False),'focus='+json.dumps(u['inputs'][1],ensure_ascii=False)]:assert s in u['answer'],s
 for i,k in enumerate(['prediction-overflow','prediction-focus']):
  v=b['reset'][k];assert v['before']['answer_open'];blank(v['after']);assert v['after']['inputs']==['編集後' if j==i else v['before']['inputs'][j] for j in range(2)]
 blank(b['condition_reset']);assert b['condition_reset']['inputs']==['',''] and b['condition_reset']['measurement']==''
 f=b['communication_failure'];assert f['status']=='COMMUNICATION_FAILURE' and f['raw']==dict(reason='HTTP 503') and f['answer']=='' and not f['answer_visible']
 s=b['stale'];assert s['before_release']['raw']==s['after_release']['raw'] and s['before_release']['answer']==s['after_release']['answer'] and s['after_release']['ignored']=='古い結果の無視: 1';blank(s['edit_after_release']);assert s['edit_after_release']['ignored']=='古い結果の無視: 2'
 assert b['console']==[] and len(b['primary_links'])==2 and all('w3.org/WAI/WCAG22/Understanding/' in x['url'] for x in b['primary_links'])
def verify():
 r=read('evidence/observations.json');b=read('evidence/browser.json');measured(r);ui(r,b)
 measured(read('evidence/observations-attempt-01.json'),P/'evidence/source-attempt-01')
 measured(read('evidence/observations-attempt-02.json'),P/'evidence/source-attempt-02')
 oracle=read('oracle.json')
 for cid,w,h,outline,covered in LITERAL:assert oracle[cid]==dict(tab_order=ORDER,horizontal_overflow=h,outline=outline,send_covered=covered,zoom='UNMEASURED')
 c=read('evidence/contract-before-producer.json');assert c['fixture_mtime_max_ns']<c['producer_initial_mtime_ns']
 for n,d in c['files'].items():assert sha(P/n)==d['sha256']
 for n,t in b['documents'].items():assert (P/n).read_text()==t,n
 for n,h in read('evidence/binding.json').items():assert sha(P/n)==h,n
 print(json.dumps(dict(status='passed',conditions=4,current_Tab=20,preserved_prior_Tab=40,ui=4,zoom='UNMEASURED',WCAG='UNASSESSED')))
if __name__=='__main__':
 if sys.argv[1:]==['--record-binding']:(P/'evidence/binding.json').write_text(json.dumps({str(f.relative_to(P)):sha(f) for f in P.rglob('*') if f.is_file() and str(f.relative_to(P))!='evidence/binding.json'},indent=2)+'\n')
 else:verify()

import json,hashlib,sys,re,copy
from pathlib import Path
from oracle import check
P=Path(__file__).resolve().parent
def validate_browser(b):
    cases=json.loads((P/'cases.json').read_text());custom=json.loads((P/'custom-oracle.json').read_text());literal=json.loads((P/'oracle.json').read_text())
    assert len(b['cases'])==len(cases)+len(custom)
    for c,item in zip(cases+custom,b['cases']):
        raw=item['raw'];r=raw['result'];rows=literal[c['id']] if c in cases else c['rows'];check(r,c['input'],rows)
        assert item['id']==c['id'] and item['status']==r['status']
        if r['status']=='OK':
            assert len(raw['draws'])==len(r['trace']) and item['answer_visible']
            assert len(item['table'])==len(r['trace'])
            maximum=max(1,max(float(__import__('fractions').Fraction(row[k])) for row in r['trace'] for k in ['previous','current','render']))
            scale=min(4,760/maximum)
            for row,draw,dom in zip(r['trace'],raw['draws'],item['table']):
                assert dom==[str(row[k]) for k in ['frame','syntheticMs','previous','current','remainderMs','alpha','render','stateAfterRender']]
                from fractions import Fraction as F
                assert draw['frame']==row['frame'] and draw['syntheticMs']==row['syntheticMs'] and draw['render']==row['render']
                assert draw['scale']==scale and draw['markerPixelX']==40+int(float(F(row['render']))*scale+0.5) and draw['markerPixelY']==200
                assert draw['rgba']==[221,68,0,255] and isinstance(draw['rafTimestampMs'],(int,float)) and draw['rafTimestampMs']>0 and 'T' in draw['wallUTC']
                assert f"frame{row['frame']}: previous {row['previous']}, current {row['current']}, alpha {row['alpha']} → 描画 {row['render']}。描画後state {row['stateAfterRender']}。" in item['answer']
            assert raw['syntheticClock']=='fixture integer ms; never rAF delta'
        else:assert not item['answer_visible'] and item['answer']=='' and item['table']==[] and raw['draws']==[]
    for key in ['prediction','next','override','condition','refused','invalid_json']:
        assert b['reset'][key]['passed'],key
    assert b['stale']['old_ignored'] and b['stale']['new_retained'] and b['stale']['edit_old_ignored']
    assert b['console']==[]
def verify():
    pointer=json.loads((P/'evidence/current.json').read_text());rawpath=P/'evidence'/pointer['raw'];assert hashlib.sha256(rawpath.read_bytes()).hexdigest()==pointer['sha256']
    raw=json.loads(rawpath.read_text());cases=json.loads((P/'cases.json').read_text());custom=json.loads((P/'custom-oracle.json').read_text());lit=json.loads((P/'oracle.json').read_text());assert len(raw['attempts'])==19
    for c,a in zip(cases+custom,raw['attempts']):
        r=json.loads(a['stdout'])['result'];check(r,c['input'],lit[c['id']] if c in cases else c['rows']);assert a['id']==c['id'] and a['exit']==(0 if r['status']=='OK' else 2) and a['stderr']==''
    for f,h in raw['source_sha256'].items():
        assert hashlib.sha256((P/f).read_bytes()).hexdigest()==h,f
    browser=json.loads((P/'evidence/browser.json').read_text());validate_browser(browser)
    for name,content in browser['documents'].items():
        target=P/'../../../subjects/game-engine-interactive-simulation/README.md' if name=='reference' else P/name
        assert target.read_text()==content,name
    binding=json.loads((P/'evidence/binding.json').read_text())
    for f,h in binding.items():assert hashlib.sha256((P/f).read_bytes()).hexdigest()==h,f
    print(json.dumps(dict(status='passed',actual_children=19,actual_browser_cases=19,actual_raf_draws=27,source_binding=True,subject_complete=False)))
if __name__=='__main__':
    if sys.argv[1:]==['--record-binding']:
        names=[str(f.relative_to(P)) for f in P.rglob('*') if f.is_file() and str(f.relative_to(P))!='evidence/binding.json']
        (P/'evidence/binding.json').write_text(json.dumps({n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in sorted(names)},indent=2)+'\n')
    else:verify()

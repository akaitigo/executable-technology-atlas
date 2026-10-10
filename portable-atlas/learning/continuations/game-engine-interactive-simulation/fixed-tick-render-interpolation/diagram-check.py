import json
from pathlib import Path
from fractions import Fraction as F
from oracle import check
P=Path(__file__).resolve().parent
exp=json.loads((P/'evidence/diagram-expectations.json').read_text());obs=json.loads((P/'evidence/diagram-probes.json').read_text());assert len(exp)==len(obs)==4
for c,o in zip(exp,obs):
    assert c['id']==o['id'];r=o['raw']['result'];check(r,c['input'],c['rows']);assert o['status']=='OK' and o['answer_visible']
    scale=min(4,760/max(1,max(float(F(row[k])) for row in r['trace'] for k in ['previous','current','render'])))
    for row,draw in zip(r['trace'],o['raw']['draws']):
        assert draw['rgba']==[221,68,0,255] and draw['scale']==scale and draw['markerPixelX']==40+int(float(F(row['render']))*scale+0.5) and 0<=draw['markerPixelX']<880
        assert draw['syntheticMs']==row['syntheticMs'] and draw['render']==row['render'] and draw['rafTimestampMs']>0
        assert 'alpha '+row['alpha']+' → 描画 '+row['render'] in o['answer']
print(json.dumps(dict(status='passed',actual_browser_diagram_probes=4,actual_extra_draws=11)))

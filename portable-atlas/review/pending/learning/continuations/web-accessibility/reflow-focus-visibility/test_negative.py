import copy,json
from checker import read,measured,ui
r=read('evidence/observations.json');b=read('evidence/browser.json');measured(r);ui(r,b)
mutants=[]
def test(name,fn):
 rr,bb=copy.deepcopy(r),copy.deepcopy(b);fn(rr,bb)
 try:measured(rr);ui(rr,bb)
 except (AssertionError,KeyError,TypeError):mutants.append(name);return
 raise AssertionError('survived '+name)
test('320-is-zoom',lambda r,b:r.update(zoom='400%'))
test('fixed-narrow-no-overflow',lambda r,b:r['cases'][1]['initial']['document'].update(scrollWidth=320))
test('fluid-narrow-overflow',lambda r,b:r['cases'][3]['initial']['document'].update(scrollWidth=760))
test('viewport-request-is-measurement',lambda r,b:r['cases'][1]['initial']['viewport'].update(clientWidth=1000))
test('Tab-order-reversed',lambda r,b:r['cases'][0]['tabs'][1]['measurement']['active'].update(id='category'))
test('untrusted-Tab',lambda r,b:r['cases'][0]['tabs'][0]['measurement']['keyEvents'][0].update(trusted=False))
test('focus-outline-fabricated',lambda r,b:r['cases'][1]['tabs'][-1]['measurement']['active'].update(outlineWidth='3px'))
test('covered-is-visible',lambda r,b:r['cases'][0]['tabs'][-1]['measurement']['active'].update(centerHitIsActive=True))
test('hit-test-null-is-clear',lambda r,b:r['cases'][1]['tabs'][-1]['measurement']['active'].update(centerHit={'id':'send','tag':'BUTTON'}))
test('overlap-zero',lambda r,b:r['cases'][0]['tabs'][-1]['measurement']['cover'].update(activeOverlapArea=0))
test('AX-inferred-from-DOM',lambda r,b:r['cases'][0]['tabs'][-1].update(nativeAX='DOM id send'))
test('control-dropped',lambda r,b:r['cases'][3]['initial']['controls'].pop())
test('partial-viewport-rounded-to-visible',lambda r,b:r['cases'][1]['tabs'][0]['measurement']['controls'][0].update(visibleViewport=True))
test('submit-not-observed',lambda r,b:r['cases'][0].update(submitted='合成送信回数: 0'))
test('single-change-causality',lambda r,b:b['cases'][0].update(answer=b['cases'][0]['answer'].replace('幅の流動化単独がfocus/遮蔽を修復した証拠ではない','幅だけで修復した')))
test('stale-applied',lambda r,b:b['stale']['after_release'].update(raw=None))
test('reset-retained',lambda r,b:b['reset']['prediction-focus']['after'].update(answer='old answer'))
test('503-shows-answer',lambda r,b:b['communication_failure'].update(answer_visible=True))
print(json.dumps(dict(status='passed',mutants_rejected=len(mutants),mutants=mutants)))

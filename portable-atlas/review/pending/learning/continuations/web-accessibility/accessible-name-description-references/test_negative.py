import copy,json
from checker import audit,read
r=read('evidence/observations.json');b=read('evidence/browser.json');audit(r,b)
mutants=[]
def test(name,change):
 rr,bb=copy.deepcopy(r),copy.deepcopy(b);change(rr,bb)
 try:audit(rr,bb)
 except (AssertionError,KeyError,TypeError):mutants.append(name);return
 raise AssertionError('survived '+name)
test('visible-is-name',lambda r,b:r['cases'][1]['name'].update(value='保存'))
test('hidden-always-excluded',lambda r,b:r['cases'][4]['queries'].update({'非表示ラベル':0}))
test('hidden-child-always-included',lambda r,b:r['cases'][7]['name'].update(value='表ラベル秘密'))
test('IDREF-order-reversed',lambda r,b:r['cases'][9]['name'].update(value='第一 第二'))
test('description-filled-from-spec',lambda r,b:r['cases'][5]['description'].update(status='OBSERVED',value='非表示の補足'))
test('description-empty-means-unobserved',lambda r,b:r['cases'][0]['description'].update(value=''))
test('browser-version-guessed',lambda r,b:r['environment'].update(browser_version='guessed'))
test('unnamed-star',lambda r,b:r['cases'][11]['name'].update(value='★'))
test('query-fabricated',lambda r,b:r['cases'][2]['queries'].update({'不一致の候補':1}))
test('click-not-performed',lambda r,b:r['cases'][11].update(clicks='操作回数: 0'))
test('wrong-prediction-erased',lambda r,b:r['cases'][1]['prediction'].update(name_match=True))
test('hardcoded-answer',lambda r,b:b['cases'][4].update(answer=b['cases'][0]['answer']))
test('stale-applied',lambda r,b:b['stale']['after_release'].update(raw=None))
test('reset-retained',lambda r,b:b['reset']['prediction-name']['after'].update(answer='old answer'))
test('transport-failure-displays-answer',lambda r,b:b['communication_failure'].update(answer_visible=True))
test('native-AX-erased',lambda r,b:r['cases'][4].update(nativeAX='DOM says 非表示ラベル'))
print(json.dumps(dict(status='passed',mutants_rejected=len(mutants),mutants=mutants)))

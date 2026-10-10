"""Independent Fraction-based hand table. No runner import; own event partition."""
from fractions import Fraction
EXPECTED={
 'unequal-volume':(9,1,10,0,[],Fraction(9,10),Fraction(1,2),Fraction(1),Fraction(0),Fraction(1)),
 'all-success':(10,0,10,0,[],Fraction(1),Fraction(1),Fraction(1),Fraction(1),Fraction(0)),
 'budget-breach':(8,2,10,0,[],Fraction(4,5),Fraction(1,2),Fraction(1),Fraction(-1),Fraction(2)),
 'expected-failures':(9,1,10,2,[],Fraction(9,10),Fraction(1,2),Fraction(1),Fraction(0),Fraction(1)),
 'window-boundaries':(3,1,4,0,['e5'],Fraction(3,4),Fraction(3,4),Fraction(2,5),Fraction(-3,5),Fraction(5,2))
}
REJECT={'zero-events':'zero-events','empty-window':'zero-eligible-window','all-expected':'zero-eligible-window','late-input':'late-input'}
def f(x):return Fraction(x['numerator'],x['denominator'])
def audit(raw):
    case=raw['case']
    if case in REJECT:
        assert raw.get('rejected')==REJECT[case];assert 'summary' not in raw
        return {'validScenario':True,'status':'rejected','reason':REJECT[case]}
    assert 'rejected' not in raw
    g,b,n,excluded,outside,sli,naive,allowed,remaining,burn=EXPECTED[case];s=raw['summary']
    assert (s['good'],s['bad'],s['denominator'],s['excluded'],s['outsideIds'])==(g,b,n,excluded,outside)
    assert [f(s[k]) for k in ('sli','naiveUnweightedSLI','allowedErrors','remainingErrors','burnRate')]==[sli,naive,allowed,remaining,burn]
    assert f(s['errorRate'])==Fraction(b,n) and s['meetsToySLO']==(sli>=Fraction(9,10))
    for raw_window,begin in zip(raw['windows'],(0,10)):
        assert raw_window['window']==[begin,begin+10]
        events={e['id']:e for e in raw['input'] if e['at']//10==begin//10 and e['at']<20}
        good={k for k,e in events.items() if e['kind']=='success'}
        bad={k for k,e in events.items() if e['kind']=='server_error'}
        removed={k for k,e in events.items() if e['kind']=='expected_rejection'}
        population=good|bad
        assert set(raw_window['allIds'])==set(events) and set(raw_window['eligibleIds'])==population and set(raw_window['excludedIds'])==removed
        assert (raw_window['good'],raw_window['bad'],raw_window['denominator'])==(len(good),len(bad),len(population))
        assert f(raw_window['sli'])==Fraction(len(good),len(population))
        assert f(raw_window['burnRate'])==Fraction(len(bad),len(population))/Fraction(1,10)
        assert f(raw_window['allowedErrors'])==Fraction(len(population),10)
        assert f(raw_window['remainingErrors'])==Fraction(len(population),10)-len(bad)
    return {'validScenario':True,'status':'calculated','exactSLI':str(sli),'naiveSLI':str(naive),'naiveWrong':sli!=naive,'burnRate':str(burn),'remainingErrors':str(remaining)}

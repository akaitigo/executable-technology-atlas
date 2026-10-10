"""独立timeline oracle。modelをimportせずprefix/sliceの閉形式を使う。"""
BASE=[{'device':d,'seq':s,'raw':s*100+(10 if d=='b' else 0)} for s in range(1,5) for d in ('a','b')]
LOCATORS={'mqtt':'https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html','coap':'https://www.rfc-editor.org/rfc/rfc7252.html','security':'https://csrc.nist.gov/pubs/ir/8259/a/final','update':'https://www.rfc-editor.org/rfc/rfc9019.html'}
def expected(capacity,policy,order,copies,sensor):
    offline=[r for r in BASE[2:] if not(sensor=='invalid-sensor' and r['device']=='a' and r['seq']==3)]
    retained=offline[-capacity:] if policy=='drop-oldest' else offline[:capacity]
    lost=offline[:-capacity] if policy=='drop-oldest' else offline[capacity:]
    deliveries=BASE[:2]+(retained if order=='forward' else retained[::-1])*copies
    reasons=[];latest=[]
    for i,r in enumerate(deliveries):
        prefix=deliveries[:i];previous=[x for x in prefix if x['device']==r['device']]
        duplicate=any((x['device'],x['seq'])==(r['device'],r['seq']) for x in prefix)
        stale=bool(previous) and r['seq']<=max(x['seq'] for x in previous)
        reasons.append('duplicate' if duplicate else 'stale' if stale else 'accept')
        snapshot={}
        for d in ('a','b'):
            group=[x for x in deliveries[:i+1] if x['device']==d]
            if group:snapshot[d]=max(group,key=lambda x:x['seq'])
        latest.append(snapshot)
    accepted=[r for r,reason in zip(deliveries,reasons) if reason=='accept']
    naiveLatest={d:next(r for r in reversed(deliveries) if r['device']==d) for d in ('a','b')}
    queueTimeline=[]
    for i in range(8):
        prefix=[r for r in offline if BASE.index(r)<=i]
        queueTimeline.append(prefix[-capacity:] if policy=='drop-oldest' else prefix[:capacity])
    return {'retained':retained,'dropped':lost,'rejected':[{'device':'a','seq':3,'raw':1001}] if sensor=='invalid-sensor' else [],'deliveries':deliveries,'reasons':reasons,'latestTimeline':latest,'accepted':accepted,'latest':latest[-1],'naiveLatest':naiveLatest,'queueTimeline':queueTimeline}
# Hand calculation at two meaningful extremes: reversed replay with all retained,
# and one-slot reject-newest. No generated expectations are used here.
HAND=[{'input':[6,'drop-oldest','reverse',2,'valid'],'protectedCount':4,'naiveCount':14,'duplicates':6,'stale':4,'latestSeq':{'a':4,'b':4},'naiveSeq':{'a':2,'b':2}}, {'input':[1,'reject-newest','forward',1,'valid'],'protectedCount':3,'naiveCount':3,'duplicates':0,'stale':0,'latestSeq':{'a':2,'b':1},'naiveSeq':{'a':2,'b':1}}]

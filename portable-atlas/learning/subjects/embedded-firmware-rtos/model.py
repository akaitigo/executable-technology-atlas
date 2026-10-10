"""Finite single-core ISR/main-loop model; logical steps/ticks, not device timing."""
import hashlib,json
SCHEDULES={'main-first':['MR','MW','IR','IW'],'preempt-main':['MR','IR','IW','MW'],'isr-first':['IR','IW','MR','MW'],'invalid-isr':['IR','MR','IW','MW']}
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def admissible(order):
    return isinstance(order,list) and all(isinstance(op,str) for op in order) and sorted(order)==['IR','IW','MR','MW'] and order.index('MR')<order.index('MW') and order.index('IR')<order.index('IW') and order.index('IW')==order.index('IR')+1

def counter(order,mode='naive'):
    if mode not in ['naive','critical'] or not admissible(order):raise ValueError('input: unsupported single-core ISR schedule')
    value=0;registers={'M':None,'I':None};trace=[];masked=False;pending=False;executed=[]
    def execute(op,source):
        nonlocal value,masked
        actor=op[0];before=value
        if op[1]=='R':registers[actor]=value
        else:value=registers[actor]+1
        if mode=='critical' and op=='MR':masked=True
        if mode=='critical' and op=='MW':masked=False
        executed.append(op)
        trace.append({'step':len(trace),'op':op,'source':source,'before':before,'after':value,'registerM':registers['M'],'registerI':registers['I'],'irqMasked':masked})
    for position,op in enumerate(order):
        if mode=='critical' and op=='IR' and masked:
            pending=True;trace.append({'step':len(trace),'op':'IRQ-deferred','source':'request index %d'%position,'before':value,'after':value,'irqMasked':True});continue
        if pending and op=='IW':continue
        execute(op,'request index %d'%position)
        if op=='MW' and pending:
            execute('IR','after unlock');execute('IW','after unlock');pending=False
    return {'mode':mode,'requestedOrder':order,'executedOrder':executed,'counter':value,'expectedIncrements':2,'lostUpdate':value!=2,'trace':trace,'traceSha256':digest(trace)}

def latency(mode='critical',hold=3,arrival=1,deadline=3):
    if mode not in ['naive','critical'] or any(type(x) is not int for x in [hold,arrival,deadline]) or not 2<=hold<=10 or not 0<=arrival<=12 or not 1<=deadline<=12:raise ValueError('input')
    unlock=hold if mode=='critical' else 0
    start=max(arrival,unlock);complete=start+1;wait=start-arrival;response=complete-arrival
    events=[{'tick':arrival,'event':'IRQ-request'},{'tick':start,'event':'ISR-start'},{'tick':complete,'event':'ISR-complete'},{'tick':arrival+deadline,'event':'relative-deadline'}]
    if mode=='critical':events.extend([{'tick':0,'event':'mask IRQ'},{'tick':hold,'event':'unmask IRQ'}])
    priority={'mask IRQ':0,'IRQ-request':1,'unmask IRQ':2,'ISR-start':3,'ISR-complete':4,'relative-deadline':5}
    events.sort(key=lambda e:(e['tick'],priority[e['event']]))
    return {'mode':mode,'maskInterval':[0,unlock],'intervalSemantics':'lower inclusive, upper exclusive','arrival':arrival,'start':start,'complete':complete,'wait':wait,'response':response,'deadline':deadline,'meetsDeadline':response<=deadline,'events':events,'eventsSha256':digest(events)}

def experiment(schedule='preempt-main',mode='naive',hold=3,arrival=1,deadline=3):
    if schedule not in SCHEDULES:raise ValueError('input')
    requested=SCHEDULES[schedule]
    selected={'counter':counter(requested,mode),'latency':latency(mode,hold,arrival,deadline)}
    return {'input':{'schedule':schedule,'mode':mode,'hold':hold,'arrival':arrival,'deadline':deadline},'selected':selected,'naive':{'counter':counter(requested,'naive'),'latency':latency('naive',hold,arrival,deadline)},'critical':{'counter':counter(requested,'critical'),'latency':latency('critical',hold,arrival,deadline)}}

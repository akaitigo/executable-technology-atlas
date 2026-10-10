"""合成記録の有限store-forward。実device/broker/networkは使わない。"""
import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES={'mqtt':'https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html','coap':'https://www.rfc-editor.org/rfc/rfc7252.html','security':'https://csrc.nist.gov/pubs/ir/8259/a/final','update':'https://www.rfc-editor.org/rfc/rfc9019.html'}
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(o):return hashlib.sha256(canonical(o).encode()).hexdigest()
def validate_record(r):
    if type(r)is not dict or set(r)!={'device','seq','raw'}:raise ValueError('record schema')
    if r['device'] not in ('a','b'):raise ValueError('unsupported device')
    if type(r['seq'])is not int or not 1<=r['seq']<=99:raise ValueError('seq integer 1..99')
    if type(r['raw'])is not int or not 0<=r['raw']<=1000:raise ValueError('sensor raw integer 0..1000')
def validate_input(capacity,policy,order,copies,sensor):
    if type(capacity)is not int or not 1<=capacity<=6:raise ValueError('capacity integer 1..6')
    if policy not in ('drop-oldest','reject-newest'):raise ValueError('unsupported overflow policy')
    if order not in ('forward','reverse'):raise ValueError('unsupported replay order')
    if type(copies)is not int or not 1<=copies<=3:raise ValueError('copies integer 1..3')
    if sensor not in ('valid','invalid-sensor'):raise ValueError('unsupported sensor fixture')
def receive(deliveries,mode):
    if mode not in ('protected','naive','fault-global-key','fault-no-monotonic'):raise ValueError('unsupported receiver')
    seen=set();latest={};accepted=[];trace=[]
    for index,r in enumerate(deliveries):
        validate_record(r);key=r['seq'] if mode=='fault-global-key' else (r['device'],r['seq']);previous=latest.get(r['device']);reason='accept'
        if mode!='naive':
            if key in seen:reason='duplicate'
            elif mode!='fault-no-monotonic' and previous and r['seq']<=previous['seq']:reason='stale'
            seen.add(key) # stale arrival is remembered too; next copy is duplicate
        if reason=='accept':latest[r['device']]=copy.deepcopy(r);accepted.append(copy.deepcopy(r))
        trace.append({'index':index,'record':copy.deepcopy(r),'previous':copy.deepcopy(previous),'decision':reason,'latest':copy.deepcopy(latest)})
    return {'mode':mode,'accepted':accepted,'latest':latest,'counts':{label:sum(t['decision']==label for t in trace) for label in ('accept','duplicate','stale')},'trace':trace,'traceSha256':digest(trace)}
def experiment(capacity=6,policy='drop-oldest',order='reverse',copies=2,sensor='valid'):
    validate_input(capacity,policy,order,copies,sensor)
    records=json.loads((ROOT/'telemetry.json').read_text())
    if sensor=='invalid-sensor':records[4]['raw']=1001
    queue=[];trace=[];online=[];rejected=[];dropped=[]
    for i,r in enumerate(records):
        before=copy.deepcopy(queue);conn='online' if i<2 else 'offline'
        try:validate_record(r)
        except ValueError as e:rejected.append(copy.deepcopy(r));trace.append({'step':i,'connection':conn,'record':r,'action':'invalid-sensor','error':str(e),'before':before,'after':copy.deepcopy(queue)});continue
        action='send-online'
        if conn=='online':online.append(copy.deepcopy(r))
        elif len(queue)<capacity:queue.append(copy.deepcopy(r));action='enqueue'
        elif policy=='drop-oldest':dropped.append(queue.pop(0));queue.append(copy.deepcopy(r));action='evict-oldest-and-enqueue'
        else:dropped.append(copy.deepcopy(r));action='reject-newest'
        trace.append({'step':i,'connection':conn,'record':r,'action':action,'before':before,'after':copy.deepcopy(queue)})
    retained=copy.deepcopy(queue);drain=queue if order=='forward' else list(reversed(queue))
    replay=[copy.deepcopy(r) for _ in range(copies) for r in drain]
    deliveries=online+replay
    trace.append({'step':8,'connection':'reconnected','action':'drain-and-replay','retained':retained,'replay':replay,'after':[]})
    return {'input':{'capacity':capacity,'policy':policy,'order':order,'copies':copies,'sensor':sensor},'records':records,'queue':{'trace':trace,'retained':retained,'dropped':dropped,'rejected':rejected,'afterReconnect':[],'traceSha256':digest(trace)},'deliveries':deliveries,'protected':receive(deliveries,'protected'),'naive':receive(deliveries,'naive')}

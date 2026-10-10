"""Finite complete single-register histories. Synthetic ticks, no distributed IO."""
class Invalid(Exception):pass
def validate(history):
    if not isinstance(history,list) or not 1<=len(history)<=4:raise Invalid('HISTORY_SIZE')
    ids=set();times=set()
    for operation in history:
        if not isinstance(operation,dict):raise Invalid('OP_SCHEMA')
        if 'res' not in operation or 'out' not in operation:raise Invalid('PENDING_UNSUPPORTED')
        if operation.get('op') not in ('write','read'):raise Invalid('UNKNOWN_OP')
        required={'id','client','op','inv','res','out'} | ({'arg'} if operation['op']=='write' else set())
        if set(operation)!=required or any(not isinstance(operation[k],str) or not operation[k] for k in ('id','client')):raise Invalid('OP_SCHEMA')
        if operation['id'] in ids:raise Invalid('DUPLICATE_ID')
        ids.add(operation['id'])
        if any(type(operation[k]) is not int or not 0<=operation[k]<=100 for k in ('inv','res')):raise Invalid('TIME_TYPE_RANGE')
        if operation['inv']>=operation['res']:raise Invalid('TIME_ORDER')
        for tick in (operation['inv'],operation['res']):
            if tick in times:raise Invalid('TIME_TIE_UNSUPPORTED')
            times.add(tick)
        if operation['op']=='write':
            if type(operation['arg']) is not int or not 0<=operation['arg']<=2:raise Invalid('WRITE_ARG')
            if operation['out']!='ok':raise Invalid('WRITE_RESPONSE')
        elif type(operation['out']) is not int or not 0<=operation['out']<=2:raise Invalid('READ_RESPONSE')
    for i,left in enumerate(history):
        for right in history[i+1:]:
            if left['client']==right['client'] and not (left['res']<right['inv'] or right['res']<left['inv']):raise Invalid('CLIENT_OVERLAP')
def search(history):
    trace=[]
    try:validate(history)
    except Invalid as error:return {'status':'INPUT_REJECTED','reason':str(error),'edges':[],'witnesses':[],'trace':[{'event':'input_rejected','reason':str(error)}],'response_sort':None}
    nodes={o['id']:o for o in history};edges=[[a['id'],b['id']] for a in history for b in history if a['res']<b['inv']]
    parents={name:{a for a,b in edges if b==name} for name in nodes};witnesses=[]
    def walk(prefix,state,remaining):
        if not remaining:witnesses.append(prefix);trace.append({'event':'legal_candidate','order':prefix,'state':state});return
        available=[name for name in remaining if parents[name].issubset(prefix)]
        trace.append({'event':'available','prefix':prefix,'state':state,'choices':available})
        for name in available:
            operation=nodes[name]
            if operation['op']=='read' and operation['out']!=state:
                trace.append({'event':'read_mismatch','prefix':prefix+[name],'expected':state,'returned':operation['out']});continue
            after=operation['arg'] if operation['op']=='write' else state
            trace.append({'event':'apply','prefix':prefix+[name],'before':state,'after':after})
            walk(prefix+[name],after,[n for n in remaining if n!=name])
    walk([],0,list(nodes))
    bad_order=[o['id'] for o in sorted(history,key=lambda o:o['res'])];state=0;bad_valid=True;failure=None
    for name in bad_order:
        o=nodes[name]
        if o['op']=='write':state=o['arg']
        elif state!=o['out']:bad_valid=False;failure={'operation':name,'expected':state,'returned':o['out']};break
    return {'status':'LINEARIZABLE' if witnesses else 'NOT_LINEARIZABLE','reason':None,'edges':edges,'witnesses':witnesses,'trace':trace,'response_sort':{'order':bad_order,'accepted':bad_valid,'failure':failure}}

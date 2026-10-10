"""Atlas: three in-memory update strategies; not a database transaction."""
from copy import deepcopy


def handle(context, request, store, fixture, mode):
    if mode not in ('bulk_assign', 'incremental_check', 'validate_then_apply'):
        raise ValueError('unsupported experiment mode')
    trace=[]
    def result(status, reason, fields=None):
        payload=None if fields is None else {'object_id':request['object_id'],
                                             'accepted_fields':list(fields)}
        return {'response':{'status':status,'reason':reason,'payload':payload},'trace':trace}
    trace.append('request-schema')
    if (type(request) is not dict or set(request)!={'object_id','operation','changes'} or
        type(request['object_id']) is not str or not request['object_id'] or
        type(request['operation']) is not str or type(request['changes']) is not dict or
        not request['changes'] or any(type(k) is not str or k not in fixture['fields']
                                     for k in request['changes']) or
        any(type(v) is not str or not 1<=len(v)<=80 for v in request['changes'].values())):
        return result(400,'invalid-request')
    trace.append('trusted-context-shape')
    if (type(context) is not dict or
        set(context)!={'actor_id','role','tenant_id','read_grants','write_grants'} or
        any(type(context[k]) is not str or not context[k] for k in ('actor_id','role','tenant_id')) or
        context['role'] not in fixture['writeFields'] or
        any(type(context[k]) is not list or any(type(x) is not str for x in context[k])
            for k in ('read_grants','write_grants'))):
        return result(401,'untrusted-context')
    trace.append('operation')
    if request['operation']!='update':return result(403,'unsupported-operation')
    trace.append('object-lookup')
    key=request['object_id'];record=store.get(key)
    if record is None:return result(404,'not-found')
    trace.append('tenant')
    if context['tenant_id']!=record['tenant_id']:return result(403,'tenant-mismatch')
    trace.append('write-grant')
    if key not in context['write_grants']:return result(403,'no-write-grant')
    changes=request['changes'];allowed=fixture['writeFields'][context['role']]
    if mode=='bulk_assign':
        trace.append('assign-all-requested-fields')
        record.update(deepcopy(changes))
    elif mode=='incremental_check':
        for field,value in changes.items():
            trace.append('check:'+field)
            if field not in allowed:
                trace.append('deny:'+field)
                return result(403,'field-forbidden')
            record[field]=deepcopy(value);trace.append('apply:'+field)
    else:
        for field in changes:
            trace.append('check:'+field)
            if field not in allowed:
                trace.append('deny:'+field)
                return result(403,'field-forbidden')
        candidate=deepcopy(record)
        candidate.update(deepcopy(changes));trace.append('build-candidate')
        store[key]=candidate;trace.append('replace-target-record')
    return result(200,'ok',changes)

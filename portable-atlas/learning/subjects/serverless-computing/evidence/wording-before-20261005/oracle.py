"""独立prefix-based state/result oracle。modelをimportしない。"""
BASE=[{'tenant':t,'id':key,'items':[value]} for t,key,value in [('a','e1',2),('a','e2',3),('b','e1',7),('a','e1',2),('b','e2',5),('b','e2',5)]]
LOCATORS={'reuse':'https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html','lifecycle':'https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html','retry':'https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html'}
def expected(reuse,lifetime,duplicates,payload,error,mode):
    import copy
    es=copy.deepcopy(BASE)
    if duplicates=='unique':es[3]['id']='e3';es[5]['id']='e3'
    if payload in ('empty','max'):
        for e in es:e['items']=[] if payload=='empty' else [0,9,9]
    if payload=='oversize':es[1]['items']=[1,2,3,4]
    if payload=='conflict':es[3]['items']=[9]
    group={'warm':6,'cold-each':1,'recycle-pairs':2}[reuse];rows=[]
    for i,e in enumerate(es):
        epoch=i//group+1
        scope=[j for j in range(i) if lifetime=='run-shared' or j//group+1==epoch]
        committed=[j for j in scope if rows[j]['status']=='executed' and es[j]['tenant']==e['tenant'] and es[j]['id']==e['id']]
        status='executed';result=None;called=False
        if len(e['items'])>3:status='input-rejected'
        elif committed:
            first=committed[0];status='duplicate' if es[first]['items']==e['items'] else 'conflict'
            if status=='duplicate':result=rows[first]['result']
        else:
            called=True
            if error=='handler-error' and i==4:status='handler-error'
            else:
                contributing=[j for j in range(i+1) if j//group+1==epoch and (j==i or rows[j]['called'])] if mode=='bad' else [i]
                items=[x for j in contributing for x in es[j]['items']]
                result={'tenant':e['tenant'],'items':items,'sum':sum(items),'count':len(items)}
        scratch=[x for j in range(i+1) if j//group+1==epoch and (called if j==i else rows[j]['called']) for x in es[j]['items']] if mode=='bad' else []
        rows.append({'environment':epoch,'coldInit':i%group==0,'status':status,'called':called,'result':result,'scratch':scratch})
    return {'rows':rows,'initCount':6//group,'handlerCalls':sum(x['called'] for x in rows),'statusCounts':{status:sum(r['status']==status for r in rows) for status in ('executed','duplicate','input-rejected','conflict','handler-error')}}

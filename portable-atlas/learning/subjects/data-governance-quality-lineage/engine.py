"""Finite neutral dataset contracts and lineage DAG. No policy certification."""
import hashlib,json,sys
from graphlib import TopologicalSorter,CycleError
from pathlib import Path

def raw(value): return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def sha(b): return 'sha256:'+hashlib.sha256(b).hexdigest()
def emit(event,**fields): print(json.dumps({'event':event,**fields},ensure_ascii=False),flush=True)
CONTRACT={'version':1,'required':['id','category','amount','class'],'amount_range':[0,1000000],'unique':'id','reference':['products.category','categories.id'],'classes':['public','internal']}

def run(request):
    sources=request['sources']; graph=request['graph']; columns=request['column_lineage']; cache=request.get('cache')
    bindings={'sources':{name:sha(raw(rows)) for name,rows in sources.items()},'contract':sha(raw(CONTRACT)),'lineage':sha(raw({'graph':graph,'columns':columns})),'producer':sha(Path(__file__).read_bytes())}
    emit('bind-input',bindings=bindings)
    violations=[]
    def bad(table,row,column,rule,actual,expected):
        item={'table':table,'row':row,'column':column,'rule':rule,'actual':actual,'expected':expected};violations.append(item);emit('violation',**item)
    refs=set()
    for i,row in enumerate(sources['categories'],1):
        value=row.get('id')
        if not isinstance(value,str) or not value.strip():bad('categories',i,'id','nonnull',value,'nonempty string')
        elif value in refs:bad('categories',i,'id','unique',value,'unique id')
        else:refs.add(value)
    seen=set()
    for i,row in enumerate(sources['products'],1):
        for col in CONTRACT['required']:
            value=row.get(col)
            if value is None or value=='':bad('products',i,col,'nonnull',value,'non-null/nonempty')
        for col in ('id','category','class'):
            value=row.get(col)
            if value not in (None,'') and (not isinstance(value,str) or not value.strip()):bad('products',i,col,'type',value,'nonempty string')
        amount=row.get('amount')
        if amount not in (None,''):
            if type(amount) is not int:bad('products',i,'amount','type',amount,'integer excluding bool')
            elif not 0<=amount<=1000000:bad('products',i,'amount','range',amount,[0,1000000])
        ident=row.get('id')
        if isinstance(ident,str) and ident.strip():
            if ident in seen:bad('products',i,'id','unique',ident,'unique id')
            seen.add(ident)
        category=row.get('category')
        if isinstance(category,str) and category.strip() and category not in refs:bad('products',i,'category','reference',category,'categories.id')
        classification=row.get('class')
        if classification not in (None,'') and classification not in CONTRACT['classes']:bad('products',i,'class','known-class',classification,['public','internal'])
    emit('quality-checked',violation_count=len(violations),rows=len(sources['products']))
    def report(decision,exit_code,graph_errors=None,order=None,output=None,stale=None):
        result={'decision':decision,'exit_code':exit_code,'contract':CONTRACT,'bindings':bindings,'violations':violations,'graph_errors':graph_errors or [],'order':order or [],'output':output or [],'column_lineage':columns,'stale':stale or []}
        emit(decision,exit_code=exit_code,output_rows=len(result['output']))
        return result
    if violations:return report('rejected',2)
    graph_errors=[]
    for node,spec in graph.items():
        for parent in spec['parents']:
            if parent not in graph:graph_errors.append({'kind':'orphan-node','node':node,'parent':parent})
    for link in columns:
        for endpoint in [link['target'],*link['sources']]:
            node,col=endpoint.split('.',1)
            if node not in graph or col not in graph[node]['columns']:graph_errors.append({'kind':'orphan-column','endpoint':endpoint})
    if graph_errors:
        emit('lineage-rejected',errors=graph_errors);return report('rejected',2,graph_errors)
    try:order=list(TopologicalSorter({n:s['parents'] for n,s in graph.items()}).static_order())
    except CycleError:
        graph_errors=[{'kind':'cycle'}];emit('lineage-rejected',errors=graph_errors);return report('rejected',2,graph_errors)
    # Each column input must be an ancestor dataset of its target.
    def ancestors(node):
        result=set(graph[node]['parents'])
        for p in graph[node]['parents']:result.update(ancestors(p))
        return result
    for link in columns:
        target=link['target'].split('.')[0]
        for endpoint in link['sources']:
            if endpoint.split('.')[0] not in ancestors(target):graph_errors.append({'kind':'nonancestor-column','endpoint':endpoint,'target':link['target']})
    if graph_errors:emit('lineage-rejected',errors=graph_errors);return report('rejected',2,graph_errors)
    emit('lineage-checked',order=order,column_links=len(columns))
    if cache:
        stale=[]
        for name,digest in bindings['sources'].items():
            prior=cache['bindings']['sources'].get(name)
            if prior!=digest:stale.append({'kind':'source-changed','source':name,'cached':prior,'current':digest})
        for name in ('contract','lineage','producer'):
            if cache['bindings'][name]!=bindings[name]:stale.append({'kind':name+'-changed'})
        if cache['output_digest']!=sha(raw(cache['output'])):stale.append({'kind':'cached-output-changed'})
        if stale:emit('cache-invalidated',reasons=stale);return report('invalidated',3,order=order,stale=stale)
        emit('cache-reused',output_digest=cache['output_digest']);return report('reused',0,order=order,output=cache['output'])
    groups={}
    for i,row in enumerate(sources['products'],1):
        key=row['category'];item=groups.setdefault(key,{'category':key,'amount_sum':0,'class':'public','product_rows':[]})
        item['amount_sum']+=row['amount'];item['product_rows'].append(i)
        if row['class']=='internal':item['class']='internal'
    output=[groups[k] for k in sorted(groups)]
    emit('aggregate-derived',output=output,output_digest=sha(raw(output)))
    return report('accepted',0,order=order,output=output)

if __name__=='__main__':
    result=run(json.load(sys.stdin));Path(sys.argv[1]).write_bytes(raw(result));raise SystemExit(result['exit_code'])

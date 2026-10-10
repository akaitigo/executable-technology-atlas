"""Fixed authored DAG and two pure allowlisted tools; no eval/LLM/IO tools."""
import copy,hashlib,json
class Rejected(Exception):
    def __init__(self,reason,phase,node,arg=None):self.details={'reason':reason,'phase':phase,'node':node,'arg':arg}
def execute(fixture):
    fixture=copy.deepcopy(fixture);plan=fixture['plan'];policy=fixture['policy'];trace=[];calls=[];results={};violation=False
    plan_hash=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def event(stage,**data):trace.append({'seq':len(trace)+1,'stage':stage,**data})
    def reject(reason,phase,node,arg=None):raise Rejected(reason,phase,node,arg)
    def preflight():
        if policy not in ('strict','bad-coercion','bad-promotion'):reject('POLICY','preflight',None)
        if not isinstance(plan,list) or not 1<=len(plan)<=8:reject('PLAN_SCHEMA','preflight',None)
        nodes={}
        for node in plan:
            if set(node)!= {'id','tool','args'} or not isinstance(node['id'],str) or node['id'] in nodes:reject('NODE_SCHEMA','preflight',None)
            if node['tool'] not in ('read','add'):reject('TOOL_ALLOWLIST','preflight',node['id'])
            if set(node['args'])!=(set() if node['tool']=='read' else {'left','right'}):reject('ARG_SCHEMA','preflight',node['id'])
            nodes[node['id']]=node
        dependencies={n:[] for n in nodes}
        for node in plan:
            for arg,expr in node['args'].items():
                if not isinstance(expr,dict):reject('EXPR_SCHEMA','preflight',node['id'],arg)
                if set(expr)=={'literal'}:
                    if type(expr['literal']) is not int or not -100<=expr['literal']<=100:reject('LITERAL_INT','preflight',node['id'],arg)
                elif set(expr)=={'ref','field','type'}:
                    if expr['type']!='int' or not isinstance(expr['field'],str):reject('EXPR_SCHEMA','preflight',node['id'],arg)
                    if expr['ref'] not in nodes:reject('UNKNOWN_REF','preflight',node['id'],arg)
                    dependencies[node['id']].append(expr['ref'])
                else:reject('EXPR_SCHEMA','preflight',node['id'],arg)
        order=[];active=set();done=set()
        def visit(name):
            if name in active:reject('CYCLE','preflight',name)
            if name in done:return
            active.add(name)
            for dependency in dependencies[name]:visit(dependency)
            active.remove(name);done.add(name);order.append(name)
        for node in plan:visit(node['id'])
        event('preflight_accepted',order=order,plan_hash=plan_hash)
        return nodes,order
    def dispatch(node,tool,args):
        # Add repeats argument validation immediately before actual pure tool call.
        if tool not in ('read','add'):reject('TOOL_ALLOWLIST','dispatch',node)
        if tool=='add' and (set(args)!={'left','right'} or any(type(v) is not int or not -100<=v<=100 for v in args.values())):reject('ADD_ARGS','dispatch',node)
        call={'node':node,'tool':tool,'args':copy.deepcopy(args)};calls.append(call);event('dispatch',**call)
        result=copy.deepcopy(fixture['read_result']) if tool=='read' else {'value':args['left']+args['right']}
        event('tool_result',node=node,result=copy.deepcopy(result));return result
    try:
        nodes,order=preflight()
        for name in order:
            node=nodes[name];args={}
            for arg,expr in node['args'].items():
                if 'literal' in expr:args[arg]=expr['literal'];continue
                origin=results[expr['ref']]
                if expr['field'] not in origin:reject('MISSING_FIELD','binding',name,arg)
                value=origin[expr['field']]
                if policy=='bad-coercion':
                    event('bad_coercion',node=name,arg=arg,original=value);value=int(value);violation=True
                if type(value) is not int:reject('TYPED_INT','binding',name,arg)
                if not -100<=value<=100:reject('INT_RANGE','binding',name,arg)
                args[arg]=value;event('bound',node=name,arg=arg,source=expr['ref'],field=expr['field'],value=value)
            if policy=='bad-promotion' and node['tool']=='add':
                # Deliberately bad comparison: only this fixed structured fixture is adopted.
                proposal=results['r']['proposed_plan'];args=copy.deepcopy(proposal['args']);violation=True;event('bad_promotion',node=name,proposal=proposal)
            results[name]=dispatch(name,node['tool'],args)
        final=results[order[-1]]['value'];event('end',final=final)
        return {'status':'BAD_COMPLETED' if violation else 'COMPLETED','final':final,'rejection':None,'calls':calls,'trace':trace,'results':results,'violation':violation,'authored_plan_hash':plan_hash}
    except Rejected as error:
        event('rejected',**error.details)
        return {'status':'REJECTED','final':None,'rejection':error.details,'calls':calls,'trace':trace,'results':results,'violation':violation,'authored_plan_hash':plan_hash}

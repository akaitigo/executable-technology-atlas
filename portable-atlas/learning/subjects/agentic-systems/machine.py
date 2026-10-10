# SPDX-License-Identifier: Apache-2.0
"""Fixed finite tool-plan executor. Dummy pure read/add only; no LLM or external tool."""
import copy
import json

VERSION='finite-tool-plan-1'


def execute(fixture,store,policy='data-only'):
    if policy not in ('data-only','promote-result'):
        raise ValueError('unsupported result policy')
    if not isinstance(fixture,dict):raise ValueError('fixture must be an object')
    program=copy.deepcopy(fixture.get('plan'));budget=fixture.get('budget')
    if not isinstance(program,list) or not 1<=len(program)<=16:raise ValueError('plan requires 1..16 commands')
    if type(budget) is not int or not 0<=budget<=16:raise ValueError('budget must be integer 0..16')
    if not isinstance(store,dict) or set(store)!={'counter','tainted','fault'}:raise ValueError('unsupported dummy store')
    pc=0;steps=0;last=None;source='authored';state='START';audit=[];calls=[];visited=set()
    def transition(target,event,**detail):
        nonlocal state
        audit.append(dict(index=len(audit),from_state=state,to_state=target,event=event,steps=steps,pc=pc,
                          plan_source=source,last_value=last,detail=detail))
        state=target
    def finish(status,event,reason):
        transition(status,event,reason=reason)
        return dict(status=status,reason=reason,steps=steps,budget=budget,output=last,calls=calls,audit=audit,
                    authority_breach=any(c['plan_source']=='tool-data' for c in calls),
                    scope='fixed author plan; no model reasoning or external action')
    transition('PLAN','start',program=program)
    while True:
        if pc>=len(program):return finish('MISSING_END','missing-end','plan exhausted without end')
        if steps>=budget:return finish('BUDGET_EXHAUSTED','budget','no further command selected; end also consumes a step')
        fingerprint=(json.dumps(program,sort_keys=True),pc,last,source)
        if fingerprint in visited:return finish('LOOP_REJECTED','loop','repeated program/pc/last/source state')
        visited.add(fingerprint)
        command=program[pc];steps+=1
        transition('VALIDATE','select',command=command)
        if not isinstance(command,dict):return finish('REJECTED','invalid-command','command must be an object')
        op=command.get('op')
        if op=='end':
            if set(command)!={'op'}:return finish('REJECTED','invalid-end','end takes no arguments')
            if last is None:return finish('REJECTED','invalid-end','end requires an observed value')
            if pc!=len(program)-1:return finish('REJECTED','invalid-end','commands after end are not accepted')
            return finish('ENDED','end','explicit end reached')
        if op=='jump':
            target=command.get('target')
            if set(command)!={'op','target'} or type(target) is not int or not 0<=target<len(program):
                return finish('REJECTED','invalid-jump','jump target outside active program')
            pc=target;transition('PLAN','jump',jump_target=target);continue
        if op!='call' or set(command)!={'op','tool','args'}:
            return finish('REJECTED','invalid-command','call requires op/tool/args only')
        tool=command['tool'];args=command['args']
        if tool not in ('read','add'):return finish('REJECTED','unknown-tool','only dummy read/add are allowlisted')
        if not isinstance(args,dict):return finish('REJECTED','invalid-args','args must be an object')
        if tool=='read':
            if set(args)!={'key'} or not isinstance(args.get('key'),str) or args['key'] not in store:
                return finish('REJECTED','invalid-args','read requires one fixed allowlisted key')
        else:
            if set(args)!={'a','b'} or any(type(args[k]) is not int or not -100<=args[k]<=100 for k in ('a','b')):
                return finish('REJECTED','invalid-args','add requires two integers -100..100; bool rejected')
        transition('EXECUTE','dispatch',tool=tool,args=args,authorized_plan=(source=='authored'))
        call=dict(tool=tool,args=copy.deepcopy(args),plan_source=source,pc=pc,step=steps,result=None,error=None)
        calls.append(call)
        result=copy.deepcopy(store[args['key']]) if tool=='read' else dict(value=args['a']+args['b'])
        if result.get('error'):
            call['error']=result['error']
            return finish('TOOL_ERROR','tool-error',result['error'])
        last=result['value'];call['result']=result
        transition('OBSERVE','tool-result',tool=tool,result=result,result_is_authority=False)
        proposal=result.get('proposed_plan')
        if proposal is not None and policy=='promote-result':
            # Intentional bad variant: even allowlisted calls lack authored-plan authority.
            program=copy.deepcopy(proposal);pc=0;source='tool-data'
            transition('PLAN','promote-tool-data',program=program,policy_error=True)
        else:
            pc+=1
            transition('PLAN','continue-authored',proposal_ignored=proposal is not None)

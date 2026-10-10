#!/usr/bin/env python3
"""Atlas: six finite lassos on the prerequisite atomic graph, not all fair cycles."""
import importlib.util
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('atlas_prerequisite',ROOT/'inputs/prerequisite-model.py')
model=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=model
spec.loader.exec_module(model)
TARGETS=('Next0','Next1','Enter1')
REGIMES=('none','weak-processes','strong-enter1-only','weak-processes-plus-strong-enter1')

def state_tuple(state):
    return [*state.pc,None if state.owner==-1 else state.owner]

def edges(state):
    result=[]
    for event,target in model.successors(state,'atomic'):
        alias='enter' if event['action']=='check-and-enter' else event['action']
        result.append({'action':'P%d.%s'%(event['process'],alias),'source_event':event,
                       'target':target,'process':event['process']})
    result.append({'action':'stutter','source_event':None,'target':state,'process':None})
    return result

def enabled(state):
    options=edges(state)
    return {'Next0':any(e['process']==0 for e in options),
            'Next1':any(e['process']==1 for e in options),
            'Enter1':any(e['action']=='P1.enter' for e in options)}

def walk(start,actions,segment):
    cursor=start;states=[cursor];rows=[]
    for ordinal,action in enumerate(actions):
        choices=[e for e in edges(cursor) if e['action']==action]
        if len(choices)!=1:raise ValueError('invalid edge in %s at %d: %s'%(segment,ordinal,action))
        edge=choices[0]
        rows.append({'ordinal':ordinal,'segment':segment,'from':state_tuple(cursor),
                     'to':state_tuple(edge['target']),'action':action,'process':edge['process'],
                     'source_event':edge['source_event'],'enabled':enabled(cursor),
                     'executed':{'Next0':edge['process']==0,'Next1':edge['process']==1,'Enter1':action=='P1.enter'},
                     'nonstutter_choices':[e['action'] for e in edges(cursor) if e['process'] is not None]})
        cursor=edge['target'];states.append(cursor)
    return states,rows

def graph_record():
    todo=[model.INITIAL];seen={model.INITIAL};all_edges=[]
    for state in todo:
        for edge in edges(state):
            target=edge['target']
            if target not in seen:seen.add(target);todo.append(target)
            all_edges.append({'from':state_tuple(state),'to':state_tuple(target),'action':edge['action'],
                              'process':edge['process'],'source_event':edge['source_event']})
    return {'kind':'graph','source_variant':'atomic','source_version':model.MODEL_VERSION,
            'event_alias':{'check-and-enter':'enter'},'states':[state_tuple(s) for s in todo],
            'edges':all_edges,'state_count':len(todo),'nonstutter_edges':sum(e['process'] is not None for e in all_edges),
            'added_stutter_edges':len(todo),'total_edges':len(all_edges),
            'safety_holds':all(model.invariant(s) for s in todo),'arbitrary_cycles_enumerated':False}

def analyze(case):
    if not case['cycle']:raise ValueError('cycle must be nonempty')
    prefix,p_rows=walk(model.INITIAL,case['prefix'],'prefix')
    cycle,c_rows=walk(prefix[-1],case['cycle'],'cycle')
    if cycle[-1]!=cycle[0]:raise ValueError('cycle is not closed')
    enabled_columns={t:[r['enabled'][t] for r in c_rows] for t in TARGETS}
    executed_columns={t:[r['executed'][t] for r in c_rows] for t in TARGETS}
    predicates={t:{'all_enabled':all(enabled_columns[t]),'any_enabled':any(enabled_columns[t]),
                   'any_executed':any(executed_columns[t]),
                   'weak':not all(enabled_columns[t]) or any(executed_columns[t]),
                   'strong':not any(enabled_columns[t]) or any(executed_columns[t])} for t in TARGETS}
    wf=predicates['Next0']['weak'] and predicates['Next1']['weak'];sf=predicates['Enter1']['strong']
    fair=[True,wf,sf,wf and sf]
    # The finite prefix excludes its final state: that state begins the repeated cycle.
    finite=prefix[:-1];period=cycle[:-1]
    cycle_critical=any(s.pc[1]=='critical' for s in period)
    obligations=[]
    for segment,states in [('prefix',finite),('cycle',period)]:
        for i,state in enumerate(states):
            if state.pc[1]!='waiting':continue
            later_prefix=segment=='prefix' and any(s.pc[1]=='critical' for s in finite[i+1:])
            obligations.append({'segment':segment,'position':i,'state':state_tuple(state),
                                'later_prefix_critical':later_prefix,'cycle_contains_critical':cycle_critical,
                                'eventually_critical':bool(later_prefix or cycle_critical)})
    starves=any(not o['eventually_critical'] for o in obligations)
    return {'kind':'lasso','id':case['id'],'valid':True,'prefix_actions':case['prefix'],'cycle_actions':case['cycle'],
            'prefix_states':[state_tuple(s) for s in prefix],'cycle_states':[state_tuple(s) for s in cycle],
            'prefix_rows':p_rows,'cycle_rows':c_rows,'enabled':enabled_columns,'executed':executed_columns,
            'predicates':predicates,'fairness_order':list(REGIMES),'fair':fair,
            'safety_holds':all(model.invariant(s) for s in prefix+cycle),
            'progress_obligations':obligations,'p1_starves':starves,'p1_response_holds':not starves,
            'fair_starvation_counterexample':[f and starves for f in fair],
            'infinite_execution_observed':False,'scope':'one prefix plus one repeated finite cycle'}

#!/usr/bin/env python3
"""Atlas: saved results against hand-fixed instructions, stacks, and node locations."""
import argparse,copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()

def verify(run,bind=True):
    expected=json.loads((ROOT/'expected.json').read_text());inputs=json.loads((ROOT/'inputs.json').read_text());checks=[]
    def ck(label,ok):
        checks.append({'label':label,'passed':bool(ok)})
        if not ok:raise ValueError(label)
    ck('one complete target without retry',run['collection_complete'] and not run['errors'] and run['target_count']==1 and run['target_retry']==0 and not run['target_start_unknown'])
    ck('fixed inputs unchanged',run['input_unchanged'])
    if bind:
        for n,h in run['input_sha256'].items():ck('input '+n,sha(ROOT/n)==h)
    ck('one command',len(run['commands'])==1)
    command=run['commands'][0]
    ck('actual priority before exec',command['priority']['priority']['verified_before_exec'] and command['priority']['priority']['after']>=10)
    ck('owned group identity',command['owned_pid']==command['owned_pgid']==command['priority']['pid']==command['priority']['pgid'])
    ck('successful bounded process',command['success'] and command['exit_code']==0 and not command['timed_out'] and command['timeout_seconds']==3)
    ck('process and group recovered',command['owned_process_reaped'] and command['owned_group_after']=='absent')
    if bind:
        for stream in ['stdout','stderr']:ck('full '+stream,sha(ROOT/command[stream]['path'])==command[stream]['sha256'])
        ck('parsed stdout equals saved records',[json.loads(x) for x in (ROOT/command['stdout']['path']).read_text().splitlines()]==run['records'])
    records=run['records'];ck('14 records',len(records)==14)
    env=records[0];ck('environment and CPU bound',env['kind']=='environment' and env['nice']>=10 and env['cpu_limit_seconds']==[2,2] and env['workers_created']==0 and env['pid']==command['owned_pid'])
    ck('Python interpreter recorded',env['python_executable']==run['python']['path'] and env['python_version']==run['python']['version'])
    normal=records[1:6];rejects=records[6:13]
    ck('normal case order',[c['id'] for c in normal]==[c['id'] for c in expected['normal']])
    def nodes(tree):
        result={tree['id']:tree}
        for key in ['left','right','child']:
            if key in tree:result.update(nodes(tree[key]))
        return result
    for actual,wanted,source in zip(normal,expected['normal'],inputs['normal']):
        label=actual['id'];c=actual['compiled'];v=actual['vm'];ns=nodes(actual['ast'])
        ck(label+' normal classification',actual['kind']=='case' and actual['classification']=='normal' and actual['expression']==source['expression'])
        ck(label+' independent values',actual['tree_vm_equal'] and actual['tree_value']==v['value']==wanted['value'] and v['status']=='returned' and v['diagnostic'] is None)
        ck(label+' fixed constants and instructions',c['constants']==wanted['constants'] and c['code']==wanted['code'])
        ck(label+' exact origin order',[o['node_id'] for o in c['origins']]==wanted['instruction_nodes'] and [o['pc'] for o in c['origins']]==list(range(len(c['code']))))
        ck(label+' source spans',all(o['span']==ns[o['node_id']]['span'] for o in c['origins']))
        ck(label+' exact subtree instruction ranges',{m['node_id']:m['instruction_range'] for m in c['node_mapping']}==wanted['node_ranges'])
        ck(label+' all AST nodes mapped once',len(c['node_mapping'])==len(ns) and {m['node_id'] for m in c['node_mapping']}==set(ns))
        for m in c['node_mapping']:
            ck(label+' node '+m['node_id'],m['kind']==ns[m['node_id']]['kind'] and m['span']==ns[m['node_id']]['span'])
            if m['node_id'] in wanted['groups']:ck(label+' transparent Group',m['emitted_pc'] is None and m['kind']=='Group')
            else:ck(label+' emitted pc '+m['node_id'],c['origins'][m['emitted_pc']]['node_id']==m['node_id'])
        trace=v['trace'];ck(label+' per-instruction count',len(trace)==len(wanted['code'])==v['executed_instructions'])
        ck(label+' exact stack after',[t['after'] for t in trace]==wanted['stack_after'])
        ck(label+' exact stack before',[t['before'] for t in trace]==[[]]+wanted['stack_after'][:-1])
        ck(label+' final single value',v['final_stack']==[wanted['value']] and v['max_height']==wanted['max_height'])
        for pc,t in enumerate(trace):
            ck(label+' command '+str(pc),t['pc']==pc and t['instruction']==wanted['code'][pc] and t['status']=='executed' and t['diagnostic'] is None)
            ck(label+' heights '+str(pc),t['height_before']==len(t['before']) and t['height_after']==len(t['after']))
            if t['instruction'][0]=='CONST':
                index=t['instruction'][1];ck(label+' constant lookup '+str(pc),t['constant_index']==index and t['constant_value']==wanted['constants'][index] and t['operands'] is None)
            else:ck(label+' right then left operands '+str(pc),t['operands']=={'left':t['before'][-2],'right':t['before'][-1]} and t['constant_index'] is None and t['constant_value'] is None)
        ck(label+' tree-evaluator nodes',set(t['node_id'] for t in actual['tree_trace'])==set(ns) and actual['tree_trace'][-1]['result']==wanted['value'])
    ck('rejection case order',[c['id'] for c in rejects]==[c['id'] for c in expected['rejections']])
    for c,w,i in zip(rejects,expected['rejections'],inputs['rejections']):
        v=c['vm'];label=c['id'];trace=v['trace'];last=trace[-1]
        ck(label+' classified rejection',c['classification']=='expected-rejection' and v['status']=='rejected' and v['value'] is None)
        ck(label+' fixed malformed input',c['constants']==i['constants'] and c['code']==i['code'])
        ck(label+' exact diagnostic',v['diagnostic']['code']==w['diagnostic'] and v['diagnostic']['pc']==w['pc'])
        ck(label+' unchanged rejection stack',v['final_stack']==last['before']==last['after']==w['stack'])
        ck(label+' stop at rejection',len(trace)==w['executed']+1 and v['executed_instructions']==w['executed'] and last['status']=='rejected' and last['pc']==w['pc'])
        ck(label+' preceding steps only',[t['status'] for t in trace[:-1]]==['executed']*w['executed'] and [t['pc'] for t in trace[:-1]]==list(range(w['executed'])))
    ck('batch terminator',records[-1]=={'kind':'batch-complete','normal_count':5,'rejection_count':7,'retry_count':0})
    return checks

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True,type=Path);parser.add_argument('--mutations',action='store_true');args=parser.parse_args();run=json.loads(args.run.read_text())
    try:
        checks=verify(run);mutations=[]
        changes=[('wrong-final-value',lambda r:r['records'][1]['vm'].update(value=20)),
                 ('swapped-left-right-origin',lambda r:r['records'][1]['compiled']['origins'][0].update(node_id='n1')),
                 ('wrong-intermediate-stack',lambda r:r['records'][1]['vm']['trace'][3].update(after=[14])),
                 ('Group-emits-an-op',lambda r:r['records'][2]['compiled']['node_mapping'][3].update(emitted_pc=2)),
                 ('index-instead-of-value',lambda r:r['records'][5]['vm']['trace'][0].update(constant_value=0)),
                 ('negative-index-accepted',lambda r:r['records'][7]['vm'].update(status='returned',value=2)),
                 ('underflow-popped-one',lambda r:r['records'][9]['vm']['trace'][-1].update(after=[])),
                 ('unreaped-producer',lambda r:r['commands'][0].update(owned_process_reaped=False))]
        if args.mutations:
            for name,change in changes:
                bad=copy.deepcopy(run);change(bad)
                try:verify(bad,bind=False)
                except (ValueError,KeyError,IndexError,TypeError) as e:mutations.append({'name':name,'rejected':True,'reason':str(e)})
                else:raise ValueError('mutation accepted '+name)
        print(json.dumps({'project':'Atlas','passed':True,'check_count':len(checks),'checks':checks,'mutations':mutations,'new_producer_execution':0},indent=2));return 0
    except Exception as e:
        print(json.dumps({'project':'Atlas','passed':False,'error':str(e)},indent=2));return 1

if __name__=='__main__':raise SystemExit(main())

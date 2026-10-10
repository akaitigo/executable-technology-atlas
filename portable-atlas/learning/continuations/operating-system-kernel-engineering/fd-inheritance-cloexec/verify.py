#!/usr/bin/env python3
"""Atlas: validate saved observations against the pre-implementation expectations."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent

def validate(run, check_source=True):
    expected=json.loads((ROOT/'expected.json').read_text())
    baseline=json.loads((ROOT/'records/pre-implementation.json').read_text())
    checks=[]
    def check(name,actual,wanted=True):checks.append({'name':name,'actual':actual,'expected':wanted,'pass':actual==wanted})
    check('frozen expected digest',hashlib.sha256((ROOT/'expected.json').read_bytes()).hexdigest(),baseline['files']['expected.json'])
    check('collection complete',run.get('collection_complete'))
    check('batch errors',run.get('errors'),[])
    if check_source:
        for name in ['CONTRACT.md','expected.json','sources.json','experiment.py','probe.py','verify.py']:
            check('source '+name,run.get('input_hashes',{}).get(name),hashlib.sha256((ROOT/name).read_bytes()).hexdigest())
    check('low priority',isinstance(run.get('nice'),int) and run['nice']>=10)
    check('max concurrent child',run.get('max_concurrent_children_observed'),1)
    check('temporary removed',run.get('cleanup',{}).get('temporary_directory_removed'))
    check('temporary created',run.get('cleanup',{}).get('temporary_directory_created'))
    check('case ids',[c.get('id') for c in run.get('cases',[])],[c['id'] for c in expected['cases']])
    observed_targets=observed_ebadf=dup_defaults=0
    for actual,wanted in zip(run.get('cases',[]),expected['cases']):
        name=wanted['id'];phases=actual.get('phases',[])
        check(name+' complete',actual.get('complete'))
        check(name+' errors',actual.get('errors'),[])
        check(name+' payload written',actual.get('payload_written_bytes'),8)
        check(name+' phase order',[p.get('phase') for p in phases],expected['phases'])
        check(name+' wait exit',actual.get('wait',{}).get('exit_code'),0)
        check(name+' wait normal',actual.get('wait',{}).get('exited'))
        check(name+' child reaped',actual.get('cleanup',{}).get('child_reaped'))
        check(name+' FD cleanup',actual.get('cleanup',{}).get('all_parent_owned_fds_closed'))
        check(name+' file cleanup',actual.get('cleanup',{}).get('owned_target_unlinked'))
        control=actual.get('control_pipe',{})
        check(name+' report separate',control.get('not_measured_target'))
        check(name+' report intentionally inherited',control.get('write_inheritable'))
        check(name+' parent write report closed',control.get('parent_write_end_closed'))
        try:
            before,forked,executed,parent=phases
            labels=list(wanted['cloexec'])
            check(name+' before labels',sorted(before['fds']),sorted(labels))
            initial_fds={label:before['fds'][label]['fd'] for label in labels}
            check(name+' per-phase distinct FD',len(set(initial_fds.values())),len(labels))
            opens=[x for x in actual['setup'] if x['operation']=='os.open']
            check(name+' one target open',len(opens),1)
            check(name+' setup original FD',opens[0]['fd'],initial_fds['original'])
            request=json.loads(actual['exec_call']['argv'][5])
            check(name+' exec request FDs',request['fds'],initial_fds)
            check(name+' exec request identity',request['target_identity'],actual['target_identity'])
            check(name+' exec request report FD',request['report_fd'],control['write_fd'])
            check(name+' exec observed report FD',executed['report_fd'],control['write_fd'])
            child_saved=[json.loads(line) for line in actual['child_pipe_utf8'].splitlines()]
            check(name+' pipe exactly two messages',len(child_saved),2)
            check(name+' saved child messages match phases',child_saved,[forked,executed])
            check(name+' partial log complete on success',actual['partial_child_messages'],child_saved)
            check(name+' fork pid',forked['pid'],actual['fork_returned_child_pid'])
            check(name+' fork new pid',forked['pid']!=before['pid'])
            check(name+' exec same pid',executed['pid'],forked['pid'])
            check(name+' parent same pid',parent['pid'],before['pid'])
            check(name+' child parent pid',forked['ppid'],before['pid'])
            check(name+' exec parent pid',executed['ppid'],before['pid'])
            check(name+' reaped pid',actual['wait']['pid'],forked['pid'])
            check(name+' before program',forked['program'],'atlas-fd-experiment-v1')
            check(name+' new program',executed['program'],'atlas-fd-probe-v1')
            check(name+' target identity type',len(actual['target_identity'])==2 and all(isinstance(v,str) and v.isdigit() for v in actual['target_identity']))
            expected_stages=[{x:'target' for x in labels},wanted['fork'],wanted['exec'],wanted['parent']]
            for stage,states in zip(phases,expected_stages):
                check(name+' '+stage['phase']+' labels',sorted(stage['fds']),sorted(labels))
                for label,desired in states.items():
                    row=stage['fds'][label];prefix=name+' '+stage['phase']+' '+label
                    check(prefix+' fd',row['fd'],before['fds'][label]['fd'])
                    check(prefix+' report not target',row['fd'] not in [control['read_fd'],control['write_fd']])
                    check(prefix+' state',row['status'],desired)
                    if row['status']=='target':
                        observed_targets+=1
                        check(prefix+' identity',row.get('identity'),actual['target_identity'])
                        check(prefix+' bytes',row.get('bytes_hex'),expected['payload_hex'])
                        check(prefix+' flag',row.get('cloexec'),wanted['cloexec'][label])
                    elif row['status']=='EBADF':
                        observed_ebadf+=1;check(prefix+' errno',row.get('errno'),9)
                        check(prefix+' no invented bytes','bytes_hex' not in row)
            dup=[x for x in actual['setup'] if x['operation']=='os.dup']
            check(name+' dup calls',len(dup),1 if 'duplicate' in labels else 0)
            for d in dup:
                dup_defaults+=1;check(name+' Python dup initial CLOEXEC',d['initial_cloexec'])
                check(name+' setup duplicate FD',d['fd'],initial_fds['duplicate'])
                check(name+' setup dup source FD',d['from_fd'],initial_fds['original'])
                check(name+' different descriptor',d['fd']!=d['from_fd'])
                check(name+' dup target identity',d['identity'],actual['target_identity'])
            check(name+' child closed surviving targets',sorted(executed['explicitly_closed_target_labels']),sorted(x for x,v in wanted['exec'].items() if v=='target'))
            check(name+' exact executed code',actual['exec_call']['argv'][4],(ROOT/'probe.py').read_text())
            check(name+' explicit exec env',actual['exec_call']['environment'],{'PYTHONDONTWRITEBYTECODE':'1'})
        except (ValueError,KeyError,TypeError,IndexError) as ex:
            check(name+' valid complete shape',str(ex),True)
    check('all target observations',observed_targets,21)
    check('all expected EBADF',observed_ebadf,3)
    check('Python dup defaults',dup_defaults,2)
    return {'project':'Atlas','pass':all(c['pass'] for c in checks),'checks':checks,'summary':{'checks':len(checks),'failed':sum(not c['pass'] for c in checks),'target_observations':observed_targets,'expected_EBADF':observed_ebadf,'python_dup_calls':dup_defaults,'new_native_runs':0}}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--mutations',action='store_true');args=p.parse_args()
    run=json.loads(args.run.read_text());result=validate(run)
    if args.mutations and result['pass']:
        alterations=[]
        for name in ['missing-phase','wrong-identity','wrong-pid','wrong-fd','wrong-flag','fake-bytes','incomplete','all-phase-wrong-fd','wrong-exec-request','changed-child-pipe']:
            changed=copy.deepcopy(run)
            if name=='missing-phase':changed['cases'][0]['phases'].pop()
            if name=='wrong-identity':changed['cases'][1]['phases'][2]['fds']['original']['identity']=['0','0']
            if name=='wrong-pid':changed['cases'][0]['phases'][2]['pid']+=1
            if name=='wrong-fd':changed['cases'][0]['phases'][2]['fds']['original']['fd']+=30
            if name=='wrong-flag':changed['cases'][1]['phases'][2]['fds']['original']['cloexec']=True
            if name=='fake-bytes':changed['cases'][1]['phases'][2]['fds']['original']['bytes_hex']='00'
            if name=='incomplete':changed['collection_complete']=False
            if name=='all-phase-wrong-fd':
                for phase in changed['cases'][0]['phases']:phase['fds']['original']['fd']+=30
            if name=='wrong-exec-request':
                args=changed['cases'][0]['exec_call']['argv'];req=json.loads(args[5]);req['fds']['original']+=30;args[5]=json.dumps(req)
            if name=='changed-child-pipe':
                c=changed['cases'][0];messages=[json.loads(line) for line in c['child_pipe_utf8'].splitlines()];messages[0]['pid']+=1;c['child_pipe_utf8']='\n'.join(json.dumps(m) for m in messages)+'\n'
            altered=validate(changed);alterations.append({'id':name,'rejected':not altered['pass'],'failed_checks':[c['name'] for c in altered['checks'] if not c['pass']]})
        result['mutations']=alterations;result['pass']=all(x['rejected'] for x in alterations)
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())

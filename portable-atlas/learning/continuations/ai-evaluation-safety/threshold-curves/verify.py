#!/usr/bin/env python3
"""Atlas: saved results versus handwritten ID sets and fractions; never run producer."""
import argparse,copy,hashlib,json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(run,bind=True):
    checks=[]
    def ck(name,value):
        if not value:raise ValueError(name)
        checks.append(name)
    expected=json.loads((ROOT/'expected.json').read_text())
    ck('one completed target no retry',run['collection_complete'] and run['target_count']==1 and run['exec_attempt_count']==1 and run['target_retry']==0 and not run['target_start_unknown'] and not run['errors'])
    ck('fixed input unchanged',run['input_unchanged'] and len(run['input_sha256'])==11)
    if bind:
        for name,digest in run['input_sha256'].items():ck('input '+name,sha(ROOT/name)==digest)
    command=run['commands'][0]
    ck('one command',len(run['commands'])==1)
    ck('priority applied before execution',command['priority']['priority']['verified_before_exec'] and command['priority']['priority']['after']>=10)
    ck('child recovered',command['success'] and command['exit_code']==0 and not command['timed_out'] and command['owned_process_reaped'] and command['owned_group_after']=='absent')
    if bind:
        for stream in ['stdout','stderr']:
            info=command[stream];file=ROOT/info['path'];ck(stream+' complete file',sha(file)==info['sha256'] and file.stat().st_size==info['bytes'])
        stream=[json.loads(line) for line in (ROOT/command['stdout']['path']).read_text().splitlines()]
        ck('all stdout rows preserved',stream==run['records'])
    records=run['records'];env=records[0]
    ck('28 records',len(records)==28)
    ck('CPU limit and no workers/models',env['kind']=='environment' and env['nice']>=10 and env['cpu_limit_seconds']==[2,2] and env['workers_created']==env['model_or_api_calls']==0)
    ck('two metadata records',[r['fixture'] for r in records if r['kind']=='fixture']==['main','tie'])
    for fixture,path,total,p_count,n_count in [('main','inputs/predictions.json',20,2,18),('tie','inputs/tie.json',3,2,1)]:
        source=json.loads((ROOT/path).read_text(),parse_float=Decimal)
        labels={r['id']:r['label'] for r in source['samples']};all_ids=set(labels)
        meta=next(r for r in records if r['kind']=='fixture' and r['fixture']==fixture)
        ck(fixture+' fixture source',meta['input_path']==path and meta['input_sha256']==sha(ROOT/path))
        ck(fixture+' sample exact identity',[(r['id'],r['label'],Decimal(r['score'])) for r in meta['samples']]==[(r['id'],r['label'],Decimal(r['score'])) for r in source['samples']])
        ck(fixture+' sizes',meta['sample_count']==total and meta['actual_positive_count']==p_count and meta['actual_negative_count']==n_count and meta['unique_score_count']==len(expected[fixture])-1 and meta['auc_computed'] is False)
        states=[r for r in records if r['kind']=='state' and r['fixture']==fixture]
        ck(fixture+' state count',len(states)==len(expected[fixture]))
        previous=set()
        for ordinal,(state,w) in enumerate(zip(states,expected[fixture])):
            threshold,positive,added,tp,fp,fn,tn,recall,fpr,precision=w
            wanted_ids=set(positive.split());counts={'TP':tp,'FP':fp,'FN':fn,'TN':tn};label=fixture+'/'+str(ordinal)
            ck(label+' order',state['ordinal']==ordinal)
            ck(label+' boundary kind/value',state['threshold']['kind']==('above-maximum' if threshold is None else 'at-score') and state['threshold']['value']==threshold)
            ck(label+' endpoint',state['threshold']['above_score']==expected[fixture][1][0] if threshold is None else state['threshold']['above_score'] is None)
            ck(label+' exact positive set',state['positive_ids']==sorted(wanted_ids))
            ck(label+' complete tie group / additions',state['added_ids']==sorted(added.split()))
            ck(label+' set inclusion',state['prior_is_subset'] is True and not state['removed_ids'] and previous<=wanted_ids and wanted_ids-previous==set(added.split()))
            wanted_outcomes={'TP':sorted(i for i in wanted_ids if labels[i]==1),'FP':sorted(i for i in wanted_ids if labels[i]==0),'FN':sorted(i for i in all_ids-wanted_ids if labels[i]==1),'TN':sorted(i for i in all_ids-wanted_ids if labels[i]==0)}
            ck(label+' all outcome IDs',state['ids']==wanted_outcomes)
            ck(label+' exact counts',state['counts']==counts and all(len(wanted_outcomes[k])==v for k,v in counts.items()))
            ck(label+' denominators conserved',tp+fn==p_count and fp+tn==n_count and sum(counts.values())==total)
            metrics=state['metrics']
            for key,num,den,fraction in [('recall',tp,tp+fn,recall),('fpr',fp,fp+tn,fpr),('precision',tp,tp+fp,precision)]:
                m=metrics[key]
                ck(label+' '+key+' count fraction',m['numerator']==num and m['denominator']==den and m['fraction']==fraction)
                ck(label+' '+key+' undefined policy',m['status']==('defined' if den else 'undefined-zero-denominator') and m['value']==(float(Fraction(fraction)) if fraction is not None else None))
            ck(label+' ROC axes',state['roc']=={'x_fraction':fpr,'y_fraction':recall,'x':float(Fraction(fpr)),'y':float(Fraction(recall))} and state['roc_status']=='defined')
            wanted_pr={'x_fraction':recall,'y_fraction':precision,'x':float(Fraction(recall)),'y':float(Fraction(precision))} if precision is not None else None
            ck(label+' PR axes and missing point',state['pr']==wanted_pr and state['pr_status']==('defined' if precision is not None else 'undefined-denominator'))
            previous=wanted_ids
        ck(fixture+' final includes all IDs',previous==all_ids)
    ck('terminator',records[-1]=={'kind':'batch-complete','fixture_count':2,'state_count':24,'retry_count':0})
    return checks
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);parser.add_argument('--mutations',action='store_true');args=parser.parse_args();run=json.loads(args.run.read_text())
    try:
        checks=verify(run);mutations=[]
        def state(r,f,i):return [x for x in r['records'] if x['kind']=='state' and x['fixture']==f][i]
        changes=[('undefined-precision-to-zero',lambda r:state(r,'main',0)['metrics']['precision'].update(value=0,fraction='0')),
                 ('ROC-swapped-axes',lambda r:state(r,'main',2).update(roc={'x_fraction':'1/2','y_fraction':'1/18','x':.5,'y':1/18})),
                 ('missing-ID-at-035',lambda r:state(r,'main',4)['positive_ids'].remove('p02')),
                 ('split-tie-group',lambda r:state(r,'tie',2)['added_ids'].remove('t-negative')),
                 ('strict-greater-than-at-maximum',lambda r:state(r,'main',1).update(positive_ids=[])),
                 ('FPR-wrong-total-denominator',lambda r:state(r,'main',2)['metrics']['fpr'].update(denominator=20,fraction='1/20',value=.05)),
                 ('recall-precision-confused',lambda r:state(r,'main',3)['metrics']['recall'].update(fraction='1/3',value=1/3)),
                 ('endpoint-PR-invented',lambda r:state(r,'main',0).update(pr={'x':0,'y':0,'x_fraction':'0','y_fraction':'0'}))]
        if args.mutations:
            for name,change in changes:
                bad=copy.deepcopy(run);change(bad)
                try:verify(bad,bind=False)
                except (ValueError,KeyError,IndexError,TypeError) as e:mutations.append({'name':name,'rejected':True,'reason':str(e)})
                else:raise ValueError('accepted mutation '+name)
        print(json.dumps({'project':'Atlas','passed':True,'check_count':len(checks),'checks':checks,'mutations':mutations,'producer_runs':0,'browser_starts':0},indent=2));return 0
    except Exception as e:
        print(json.dumps({'project':'Atlas','passed':False,'error':str(e)},indent=2));return 1
if __name__=='__main__':raise SystemExit(main())

"""Atlas: synthetic workplace resource boundaries; no ps, child, priority or model action."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('gate',ROOT/'resource-gate.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
policy=json.loads((ROOT/'gate-policy.json').read_text())
rows=[{'pid':1,'ppid':0,'lstart':'fixture init','comm':'/sbin/launchd','cpu':0.0}]
for item in policy['known_idle_identities']:
    rows.append({k:item[k] for k in ('pid','ppid','lstart','comm')}|{'cpu':0.0})
parent=next(r['ppid'] for r in rows if r['pid']==policy['root_coordinator_pid'])
if parent not in [r['pid'] for r in rows]:
    rows.append({'pid':parent,'ppid':1,'lstart':'fixture coordinator parent','comm':'/fixture/python3','cpu':0.0})
known=policy['required_present_pids'];cases=[]


def assessment(name,change,expected,complete=True):
    candidate=copy.deepcopy(rows);change(candidate)
    actual=gate.assess(candidate,policy,complete)
    assert actual['process_condition_passed'] is expected,(name,actual)
    cases.append({'case':name,'expected':expected,'observed':actual})


def add(comm,parent_pid=1,cpu=0.0):
    return lambda rs:rs.append({'pid':9999991,'ppid':parent_pid,'lstart':'synthetic newcomer','comm':comm,'cpu':cpu})


def edit(pid,**fields):
    return lambda rs:next(r for r in rs if r['pid']==pid).update(fields)


assessment('root-exact-idle',lambda r:None,True)
assessment('ordinary-Chrome-10-percent',add('/Applications/Google Chrome',cpu=10),True)
assessment('ordinary-Safari-9-percent',add('/Applications/Safari',cpu=9),True)
assessment('other-headless',add('/fixture/headless_shell'),False)
assessment('other-playwright',add('/fixture/playwright'),False)
assessment('unknown-root-Chrome',add('/Applications/Google Chrome',policy['root_coordinator_pid']),False)
assessment('unknown-root-python',add('/fixture/python3',policy['root_coordinator_pid']),False)
assessment('unknown-root-grandchild',add('/Applications/Safari',known[1]),False)
assessment('known-PID-reused-as-desktop',edit(known[0],comm='/Applications/Google Chrome'),False)
assessment('known-parent-changed',edit(known[0],ppid=0),False)
assessment('known-start-changed',edit(known[0],lstart='different'),False)
assessment('known-at-one-percent',edit(known[0],cpu=1.0),True)
assessment('known-over-one-percent',edit(known[0],cpu=1.1),False)
assessment('root-group-at-two',lambda r:[edit(k,cpu=1.0)(r) for k in known[:2]],True)
assessment('root-group-over-two',lambda r:[edit(k,cpu=1.0)(r) for k in known[:3]],False)
assessment('required-root-absent',lambda r:r.remove(next(x for x in r if x['pid']==known[-1])),False)
assessment('nonroot-java-purpose-unknown',add('/fixture/java'),True)
assessment('nonroot-crashpad-purpose-unknown',add('/Applications/Slack.app/chrome_crashpad_handler'),True)
assessment('nonroot-native-host-purpose-unknown',add('/fixture/native-host'),True)
assessment('nonroot-ChatGPT-Chrome-purpose-unknown',add('/fixture/ChatGPT for Chrome'),True)
assessment('nonroot-Safari-helper',add('/Applications/Safari Helper'),True)
assessment('unknown-root-native-host',add('/fixture/native-host',known[1]),False)
assessment('other-benchmark',add('/fixture/pgbench'),False)
assessment('desktop-unknown-ancestry',add('/Applications/Google Chrome',9999990),False)
assessment('desktop-cyclic-ancestry',add('/Applications/Safari',9999991),False)
assessment('nonruntime-unknown-ancestry',add('/fixture/python3',9999990),False)
assessment('nonruntime-cyclic-ancestry',add('/fixture/python3',9999991),False)
assessment('incomplete-snapshot',lambda r:None,False,False)
assessment('empty-snapshot',lambda r:r.clear(),False)
assessment('duplicate-PID',lambda r:r.append(dict(r[0])),False)
for case in cases:
    if case['case'] in ('nonroot-java-purpose-unknown','nonroot-crashpad-purpose-unknown','nonroot-native-host-purpose-unknown','nonroot-ChatGPT-Chrome-purpose-unknown'):
        entry=case['observed']['unclassified_observations'][0]
        assert entry['classification']=='unclassified_observation' and entry['allowed'] is False
        assert entry['ownership']=='nonroot' and entry['purpose']=='unknown'

base={'process_snapshot_complete':True,'process_condition_passed':True,'ps_returncode':0,'top_returncode':0,
      'memory_pressure_returncode':0,'vm_stat_returncode':0,'cpu_count':policy['cpu_count_required'],
      'load':[5.9,10,10],'top_idle_percent':75,'memory_free_percent':40,
      'available_memory_estimate_gib':2,'ps_aggregate_cpu_percent':9999}
headroom=[]
for name,delta,expected in [
    ('base-inclusive-memory',{},True),('load-equals-six',{'load':[6,0,0]},False),
    ('load-over',{'load':[6.1,0,0]},False),('load-missing',{'load':None},False),
    ('global-cpu-above-400',{'top_idle_percent':66.66},False),
    ('global-cpu-below-400',{'top_idle_percent':66.67},True),
    ('idle-below-sixty',{'top_idle_percent':59.9},False),('idle-invalid',{'top_idle_percent':101},False),
    ('free-below-forty',{'memory_free_percent':39.9},False),('estimate-below-two',{'available_memory_estimate_gib':1.999},False),
    ('estimate-missing',{'available_memory_estimate_gib':None},False),('vm-failed',{'vm_stat_returncode':1},False),
    ('memory-query-failed',{'memory_pressure_returncode':1},False),('top-failed',{'top_returncode':1},False),
    ('ps-failed',{'ps_returncode':1},False),('ancestry-blocked',{'process_condition_passed':False},False),
    ('snapshot-incomplete',{'process_snapshot_complete':False},False),('cpu-count-mismatch',{'cpu_count':99},False),
    ('ps-sum-is-auxiliary',{'ps_aggregate_cpu_percent':0},True)]:
    observed=gate.headroom(base|delta,policy);assert observed is expected,name
    headroom.append({'case':name,'expected':expected,'observed':observed})
# Exact aggregate=400 and idle=60 at an injected 10-core boundary, not a claim about this Mac.
p10={**policy,'cpu_count_required':10}
assert gate.headroom(base|{'cpu_count':10,'top_idle_percent':60},p10) is True
headroom.append({'case':'exact-400-at-injected-10-cores','expected':True,'observed':True})
desktop_rows=copy.deepcopy(rows);add('/Applications/Google Chrome',cpu=95)(desktop_rows)
desktop_class=gate.assess(desktop_rows,policy,True)
assert desktop_class['process_condition_passed'] is True
assert gate.headroom(base|desktop_class|{'top_idle_percent':50},policy) is False
headroom.append({'case':'high-desktop-classification-observed-global-refused','classification_passed':True,'expected':False,'observed':False})

vm='Mach Virtual Memory Statistics: (page size of 4096 bytes)\nPages free: 131072.\nPages inactive: 393216.\nPages speculative: 0.\n'
parsed=gate.available_memory_estimate(vm);assert parsed['available_memory_estimate_gib']==2
memory=[{'case':'exact-two-gib','observed':parsed,'passed':True}]
for name,text in [('missing-field',vm.replace('Pages inactive: 393216.\n','')),
                  ('duplicate-field',vm+'Pages free: 1.\n'),('missing-page-size',vm.replace('page size of 4096 bytes','unknown')),
                  ('bad-count',vm.replace('131072.','NaN.'))]:
    try:gate.available_memory_estimate(text)
    except ValueError as error:memory.append({'case':name,'refused':str(error),'passed':True})
    else:raise AssertionError(name)

report={'title':'Atlas workplace resource policy finite checks','passed':True,'classification_cases':cases,
        'headroom_cases':headroom,'memory_parser_cases':memory,'process_observations':0,'target_runs':0,
        'actual_priority_changed':False,'injected_CPU_count_case_is_not_machine_observation':True,
        'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['resource-gate.py','gate-policy.json','check-workplace-policy.py']}}
(ROOT/'observations/workplace-policy-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'classification_cases':len(cases),'headroom_cases':len(headroom),'memory_cases':len(memory),'target_runs':0}))

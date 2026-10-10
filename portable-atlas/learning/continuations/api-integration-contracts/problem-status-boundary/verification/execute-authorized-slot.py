"""Atlas: bind one fresh observation to the explicit root slot; no polling."""
import contextlib, datetime, hashlib, io, json, runpy, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CLASSIFICATION = ROOT.parent / 'browser-qa/csp-problem-depth-2026-10-07/decisions/api-observation-01-reviewed.json'
CLASSIFICATION_SHA = 'e6a1a6f637bd3397fde5b5594786548297ba663aa85f3dfce12071fa8b0c6567'
SLOT = 'root\u304c55b58\u2026\u5168702\u884c\u30fbroot5/5\u30fb\u5019\u88dc60\u5168identity\u3068\u8cc7\u6e90\u6761\u4ef6\u3092\u72ec\u7acb\u78ba\u8a8d\u3057\u307e\u3057\u305f\u3002\u5168\u6761\u4ef6pass\u3067\u3059\u304c\u30ec\u30d3\u30e5\u30fc\u5b8c\u4e86\u3067age67.9\u79d2\u306b\u306a\u3063\u305f\u305f\u3081\u8d77\u52d50\u3092\u4fdd\u6301\u3002\u4fdd\u5b58\u8a18\u9332 browser-qa/csp-problem-depth-2026-10-07/decisions/api-observation-01-reviewed.json\uff08allowed:false\u3001identity/resource\u306e\u307fpass\uff09\u3002\u4eca\u56deAPI\u306b\u5358\u72ec\u306e\u89b3\u6e2c\u2192\u521d\u56de\u8a08\u7b97\u67a0\u3092\u660e\u793a\u4ed8\u4e0e\u3057\u307e\u3059\u3002\u73fe\u89b3\u6e2c\u306f\u5c65\u6b74\u3078\u4fdd\u6301\u3057\u3001\u65b0\u89b3\u6e2c\u30921\u56de\u3060\u3051\u53d6\u308b\u2192\u4e0a\u8a1860identity\uff0broot5\u3068filter\u524d\u3067\u4e00\u81f4\uff08\u65b0\u898f/\u5909\u5316\u306fhold\uff09\u3001trusted\u5168ps\u3001load<6 idle>=60 memoryfree>=40 available>=2GiB aggregate<=400 knownHeavy\u7a7a\u3001browser\u5404<=1\u5408\u8a08<=2\u3001age<=60\u79d2\u3092\u3059\u3079\u3066\u78ba\u8a8d\u2192\u4eca\u56descope\u306e\u65b0decision\u3092obsSHA\u306b\u7d50\u3073allowed/rootSlot/rootGuiIdle:true\u30fbotherTargets:0\u30fbauthorization\u306b\u672croot\u6307\u793a\u3092\u8a18\u9332\u3057\u3066\u3001\u76f4\u3061\u306bexecute_once.py\u306e\u521d\u56de1\u5b50nice10/wall15/retry0\u3092\u5b9f\u884c\u53ef\u3002\u79c1\u306eGUI\u306fidle\u3001CSP/depth\u5bfe\u8c61\u8d77\u52d5\u306f\u4e0e\u3048\u307e\u305b\u3093\u3002\u6761\u4ef6\u3092\u6e80\u305f\u3055\u306a\u3051\u308c\u3070hold\u3001\u9023\u7d9a\u89b3\u6e2c\u3057\u306a\u3044\u3002\u5b8c\u4e86/\u56de\u53ce\u3092\u8fd4\u3059\u307e\u3067\u67a0\u3092\u72ec\u5360\u3057\u307e\u3059\u3002'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(CLASSIFICATION) == CLASSIFICATION_SHA
classification = json.loads(CLASSIFICATION.read_text())
pre = ROOT.parent / 'acceptance/api-problem-status-boundary/preexecution-review.json'
assert sha(pre) == '5854d9bc43a0411ffa652112894dcd96a23d4828b41ed03285328e28836762ee'
for b in json.loads(pre.read_text())['bindings']:
    assert sha(Path(b['path'])) == b['sha256']
assert not (ROOT / 'observations/run-01').exists()
observation = ROOT / 'verification/resource-before-calculation.json'
assert sha(observation) == '55b58cca9d3790e3a13b78be4a48943da0cf5e1117c51eb22e0b6de47e4a590b'
backup = observation.with_name('resource-before-classification.json')
assert not backup.exists()
observation.rename(backup)
import resource_observe
with contextlib.redirect_stdout(io.StringIO()):
    resource_observe.main()
g = json.loads(observation.read_text())
ps = g['processObservation']
identity = ('pid', 'ppid', 'lstart', 'command')
ident = lambda x: tuple(x[k] for k in identity)
all_rows = {x['pid']: x for x in ps['processes']}
browsers = ps['browsers'] or []
age = (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(g['observedAt'])).total_seconds()
checks = {
 'trusted': g['readTrusted'] is True and ps['trusted'] is True and ps['own_pid_present'] is True and not ps['parse_errors'],
 'classifiedIdentitiesBeforeFilter': all(x['pid'] in all_rows and ident(all_rows[x['pid']])==ident(x) for x in classification['identities']+classification['rootIdentities']),
 'same60BrowserIdentities': len(browsers)==60 and {ident(x) for x in browsers}=={ident(x) for x in classification['identities']},
 'root5Exact': len(classification['rootIdentities'])==5 and all(x['pid'] in all_rows and ident(all_rows[x['pid']])==ident(x) for x in classification['rootIdentities']),
 'knownHeavyEmpty': ps['heavy']==[],
 'loadBelow6': g['load'][0] < 6,
 'idleAtLeast60': g['idlePercent'] is not None and g['idlePercent']>=60,
 'memoryAtLeast40': g['memoryFreePercent'] is not None and g['memoryFreePercent']>=40,
 'availableAtLeast2GiB': g['availableMemoryEstimateGiB'] is not None and g['availableMemoryEstimateGiB']>=2,
 'aggregateAtMost400': sum(x['cpu_percent_one_core'] for x in ps['processes'])<=400,
 'browserEachAtMost1': all(x['cpu_percent_one_core']<=1 for x in browsers),
 'browserTotalAtMost2': sum(x['cpu_percent_one_core'] for x in browsers)<=2,
 'freshAtMost60': 0<=age<=60,
}
record = {'Atlas':'API consumer\u306e\u4eca\u56de\u9650\u5b9a\u5b9f\u884c\u6761\u4ef6','checks':checks,'passed':all(checks.values()),'ageSeconds':age,'oldObservation':{'path':str(backup),'sha256':sha(backup)},'newObservation':{'path':str(observation),'sha256':sha(observation)},'classification':{'path':str(CLASSIFICATION),'sha256':sha(CLASSIFICATION)},'preexecution':{'path':str(pre),'sha256':sha(pre)},'slotText':SLOT,'binderSha256':sha(Path(__file__))}
gate = ROOT/'verification/runtime-gate.json'
with gate.open('x') as f:
    json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
if not record['passed']:
    print(json.dumps({'started':False,'checks':checks,'record':str(gate)},ensure_ascii=False));raise SystemExit(1)
decision = {'Atlas':'API consumer\u306e\u5358\u72ec\u5b9f\u884c\u8a31\u53ef\u306e\u5bfe\u5fdc','scope':'api-problem-status-boundary','allowed':True,'observationSha256':sha(observation),'rootSlot':True,'rootGuiIdle':True,'otherTargets':0,'authorization':SLOT,'identities':classification['identities']+classification['rootIdentities'],'classificationSha256':sha(CLASSIFICATION),'runtimeGateSha256':sha(gate),'preexecutionSha256':sha(pre),'freshLimitSeconds':60}
dp=ROOT/'verification/runtime-decision.json'
with dp.open('x') as f:
    json.dump(decision,f,ensure_ascii=False,indent=2);f.write('\n')
assert 0 <= (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(g['observedAt'])).total_seconds() <= 60
sys.argv=[str(ROOT/'execute_once.py'),'--decision',str(dp)]
runpy.run_path(str(ROOT/'execute_once.py'),run_name='__main__')

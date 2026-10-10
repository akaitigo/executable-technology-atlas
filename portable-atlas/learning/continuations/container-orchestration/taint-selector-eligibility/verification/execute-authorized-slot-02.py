"""Atlas: bind the explicit one-run slot to one fresh observation; no polling."""
import contextlib, datetime, hashlib, io, json, os, runpy, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CLASSIFICATION = ROOT.parent / "browser-qa/type-placement-phase-2026-10-06/decisions/orchestration-taint-selector-eligibility.json"
CLASSIFICATION_SHA = "5b084e786022884d496fe03139377c76050147be124d8387353571eba63da7d4"
SLOT = "型1child exit0/reaped/group absentの返却を受領。配置だけ今次単独枠を付与。root GUI idle/通信target0/他target0。decision5b084e…の59identity同一とroot5完全一致、全ps trusted/self present、knownHeavy空、load1<6、idle>=60%、memory free>=40%、available推定>=2GiB、全CPU<=400%（1core基準）、browser各<=1%/合計<=2%を全て新freshで確認。fresh60秒以内（runnerの上限300に依存しない）で実行decisionへ新SHAとこのslot文を保存して nice>=10/1child/wall15秒/retry0の1回のみ可。review_atomicのidentity読戻しもpass後に開始。変化/不足は停止し、自動retryなし。終わり次第回収/保存検査を短報・枠返却。"
SLOT = SLOT + "\n追加の今回枠: 通信1child exit0/0.453秒/nice10/reapedの枠返却受領。配置へ新しい単独枠を付与します。これは初回holdからの自動再試行ではなく、通信工程終了後の新観測判断です。先のhold/gate/観測を別名で完全保持し、新freshを1回だけ取得、先の明示全条件＋同identity・age60秒を満たす場合のみ初回target1childを実行可。root GUI idle/他target0。同じ不足ならまた対象0停止、連続poll禁止。decisionとslot文に今回枠を記録し、回収/検査結果を返してください。"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(CLASSIFICATION) == CLASSIFICATION_SHA
classification = json.loads(CLASSIFICATION.read_text())
pre = ROOT.parent / "acceptance/orchestration-taint-selector-eligibility/preexec-review.json"
assert sha(pre) == "4177295232c5b901cf218293401be1ae4c6d8e3cdea72b640753a03875580aea"
for b in json.loads(pre.read_text())["bindings"]:
    assert sha(Path(b["path"])) == b["sha256"]
assert not (ROOT / "observations/run-01").exists()
old = ROOT / "verification/resource-before-calculation.json"
assert sha(old) == "adc610da9a39d41fa865c6b4ea4b67eecc274a280a5e08074a8b7bc9d50b2b50"
backup = old.with_name("resource-before-held-calculation.json")
assert not backup.exists()
old.rename(backup)
old_gate = ROOT / "verification/runtime-gate.json"
assert sha(old_gate) == "f7815bccd4511fae79cc4f25b92e1f57c86219170ca201174933fe7a55c0e96b"
gate_backup = old_gate.with_name("runtime-gate.first-hold.json")
assert not gate_backup.exists()
old_gate.rename(gate_backup)
import resource_observe
with contextlib.redirect_stdout(io.StringIO()):
    resource_observe.main()
g = json.loads(old.read_text()); ps = g["processObservation"]; identity = ("pid", "ppid", "lstart", "command")
ident = lambda x: tuple(x[k] for k in identity)
all_rows = {x["pid"]: x for x in ps["processes"]}
browsers = ps["browsers"] or []
age = (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(g["observedAt"])).total_seconds()
checks = {
 "trusted": g["readTrusted"] is True and ps["trusted"] is True and ps["own_pid_present"] is True and not ps["parse_errors"],
 "same59BrowserIdentities": len(browsers)==59 and {ident(x) for x in browsers}=={ident(x) for x in classification["identities"]},
 "root5Exact": len(classification["requiredRootIdentities"])==5 and all(x["pid"] in all_rows and ident(all_rows[x["pid"]])==ident(x) for x in classification["requiredRootIdentities"]),
 "knownHeavyEmpty": ps["heavy"]==[],
 "loadBelow6": g["load"][0] < 6,
 "idleAtLeast60": g["idlePercent"] is not None and g["idlePercent"]>=60,
 "memoryAtLeast40": g["memoryFreePercent"] is not None and g["memoryFreePercent"]>=40,
 "availableAtLeast2GiB": g["availableMemoryEstimateGiB"] is not None and g["availableMemoryEstimateGiB"]>=2,
 "aggregateAtMost400": sum(x["cpu_percent_one_core"] for x in ps["processes"])<=400,
 "browserEachAtMost1": all(x["cpu_percent_one_core"]<=1 for x in browsers),
 "browserTotalAtMost2": sum(x["cpu_percent_one_core"] for x in browsers)<=2,
 "freshAtMost60": 0<=age<=60,
}
record = {"Atlas":"配置模型の今回限定実行条件", "checks":checks,"passed":all(checks.values()),"ageSeconds":age,"oldObservation":{"path":str(backup),"sha256":sha(backup)},"newObservation":{"path":str(old),"sha256":sha(old)},"classification":{"path":str(CLASSIFICATION),"sha256":sha(CLASSIFICATION)},"preexecution":{"path":str(pre),"sha256":sha(pre)},"slotText":SLOT,"binderSha256":sha(Path(__file__))}
record_path=ROOT/"verification/runtime-gate.json"
with record_path.open("x") as f: json.dump(record,f,ensure_ascii=False,indent=2);f.write("\n")
if not record["passed"]:
    print(json.dumps({"started":False,"checks":checks,"record":str(record_path)},ensure_ascii=False));raise SystemExit(1)
decision = {"Atlas":"配置模型の単独実行許可の対応", "scope":"orchestration-taint-selector-eligibility","allowed":True,"observationSha256":sha(old),"rootSlot":True,"rootGuiIdle":True,"otherTargets":0,"authorization":SLOT,"identities":classification["identities"]+classification["requiredRootIdentities"],"classificationSha256":sha(CLASSIFICATION),"runtimeGateSha256":sha(record_path),"preexecutionSha256":sha(pre),"freshLimitSeconds":60}
dp=ROOT/"verification/runtime-decision.json"
with dp.open("x") as f: json.dump(decision,f,ensure_ascii=False,indent=2);f.write("\n")
assert 0 <= (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(g["observedAt"])).total_seconds() <= 60
sys.argv=[str(ROOT/"execute_once.py"),"--decision",str(dp)]
runpy.run_path(str(ROOT/"execute_once.py"),run_name="__main__")

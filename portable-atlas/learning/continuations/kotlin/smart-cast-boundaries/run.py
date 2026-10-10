#!/usr/bin/env python3
"""条件を満たす将来の枠でだけ、3compile・6runを低優先度で1batch実行する。"""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from resource_gate import assess

HERE = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bind(compiler, archive, expected):
    if sha(archive) != expected["compiler_archive_sha256"]:
        raise RuntimeError("既存の固定compiler配布物とdigestが不一致")
    tree = compiler.parent.parent
    entries = {}
    with zipfile.ZipFile(archive) as package:
        for info in package.infolist():
            if info.is_dir():
                continue
            name = Path(info.filename)
            if name.parts[0] != "kotlinc" or ".." in name.parts:
                raise RuntimeError("配布物entryが不正")
            relative = Path(*name.parts[1:]).as_posix()
            target = tree / relative
            if target.is_symlink() or not target.is_file():
                raise RuntimeError("展開済みcompilerの通常ファイルが不足")
            digest = hashlib.sha256(package.read(info)).hexdigest()
            if sha(target) != digest:
                raise RuntimeError("展開済みcompilerの内容不一致: " + relative)
            entries[relative] = digest
    if set(entries) != {p.relative_to(tree).as_posix() for p in tree.rglob("*") if p.is_file()}:
        raise RuntimeError("展開済みcompilerのファイル集合が不一致")
    if entries["bin/kotlinc"] != expected["compiler_launcher_sha256"]:
        raise RuntimeError("launcherが固定値と不一致")
    return {"tree_matches_archive": True, "tree_file_count": len(entries),
            "archive_sha256": expected["compiler_archive_sha256"],
            "launcher_sha256": entries["bin/kotlinc"]}


def main():
    parser = argparse.ArgumentParser(description="負荷条件を満たす場合だけ固定Kotlinで逐次実行")
    parser.add_argument("--compiler", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--java", required=True, type=Path)
    parser.add_argument("--attempt", type=Path, help="Unused attempt directory inside this lesson's observations")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = (HERE / args.attempt).resolve() if args.attempt else HERE / "observations" / stamp
    if out.parent != HERE / "observations" or (out / "run.json").exists():
        raise RuntimeError("Attempt must be unused and directly within this lesson's observations")
    out.mkdir(parents=True, exist_ok=args.attempt is not None)
    gate = assess()
    (out / "resource-gate.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n")
    if not gate["allowed"]:
        print(json.dumps({"execution": "not-run", "gate": str(out.relative_to(HERE) / "resource-gate.json")}, ensure_ascii=False))
        return 2
    compiler, archive, java = (p.resolve() for p in (args.compiler, args.archive, args.java))
    expected = json.loads((HERE / "expected.json").read_text())
    names = ["expected.json", "sources.json", "run.py", "resource_gate.py",
             "src/SnapshotAndContrast.kt", "src/MutablePropertyRejected.kt", "src/CustomGetterRejected.kt"]
    report = {"schema": "atlas.kotlin-smart-cast-boundaries.observation.v1",
              "started_at": datetime.now(timezone.utc).isoformat(),
              "source_sha256": {name: sha(HERE / name) for name in names},
              "resource_gate": gate, "compiles": [], "runs": [], "commands": [], "errors": [],
              "global_concurrency_guarantee": False, "all_properties_covered": False,
              "execution_policy": {"sequential": True, "nice_increment": 10, "compiler_heap_mib": 256,
                                   "active_processor_count": 1, "batch_budget_seconds": 45,
                                   "per_command_timeout_seconds": 15, "runtime_heap_mib": 64,
                                   "representative_first": True, "retries": 0}}
    env = os.environ.copy()
    for key in ("CLASSPATH", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS",
                "KOTLIN_HOME", "KOTLIN_RUNNER", "KOTLIN_COMPILER", "KOTLIN_TOOL"):
        env.pop(key, None)
    env.update({"LC_ALL": "C", "LANG": "C", "JAVACMD": str(java),
                "JAVA_OPTS": "-Xms32m -Xmx256m -XX:ActiveProcessorCount=1"})
    deadline = time.monotonic() + 45
    (out / "priority").mkdir()

    def save_report():
        (out / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    def execute(label, command):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("batch全体の時間上限に到達")
        before = time.monotonic()
        receipt = out / "priority" / (label + ".json")
        proc = subprocess.Popen([sys.executable, str(HERE / "run.py"), "--priority-child", str(receipt), *command],
                                cwd=HERE, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, start_new_session=True)
        timed_out = False
        try:
            stdout, stderr = proc.communicate(timeout=min(15, remaining))
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate(timeout=2)
        try:
            os.killpg(proc.pid, 0)
            group_remaining = True
        except ProcessLookupError:
            group_remaining = False
        if group_remaining:
            os.killpg(proc.pid, signal.SIGKILL)
        display = [str(x).replace(str(compiler), "<kotlinc-2.4.10>").replace(str(java), "<java-17>")
                   .replace(str(compiler.parent.parent), "<kotlinc-home>") for x in command]
        item = {"label": label, "command": display, "nice_increment": 10,
                "exit_code": proc.returncode, "stdout": stdout, "stderr": stderr,
                "elapsed_seconds": round(time.monotonic() - before, 6), "attempt": 1, "retry": 0,
                "timed_out": timed_out, "owned_process_group_remaining_after_exit": group_remaining,
                "priority_observation": json.loads(receipt.read_text()) if receipt.exists() else None}
        report["commands"].append(item)
        if timed_out or group_remaining:
            raise RuntimeError(label + ": timeout or remaining owned child group; stopped without retry")
        if not item["priority_observation"] or item["priority_observation"]["after"] < 10:
            raise RuntimeError(label + ": low priority was not confirmed; stopped without retry")
        return item
    try:
        report["toolchain"] = bind(compiler, archive, expected)
        report["compiler_probe"] = execute("compiler-version", [str(compiler), "-version"])
        report["java_probe"] = execute("java-version", [str(java), "-version"])
        if report["compiler_probe"]["exit_code"] != 0 or "kotlinc-jvm 2.4.10" not in report["compiler_probe"]["stdout"] + report["compiler_probe"]["stderr"]:
            raise RuntimeError("compiler実version不一致")
        if report["java_probe"]["exit_code"] != 0 or 'version "17.0.17"' not in report["java_probe"]["stdout"] + report["java_probe"]["stderr"]:
            raise RuntimeError("OpenJDK実version不一致")
        flags = ["-language-version", "2.4", "-api-version", "2.4", "-jvm-target", "17", "-Xrender-internal-diagnostic-names"]
        compile_inputs = [("snapshot-and-contrast", "src/SnapshotAndContrast.kt"),
                          ("mutable-property-rejected", "src/MutablePropertyRejected.kt"),
                          ("custom-getter-rejected", "src/CustomGetterRejected.kt")]
        def compile_case(case_id, source):
            jar = out.relative_to(HERE) / (case_id + ".jar")
            item = execute(case_id, [str(compiler), source, *flags, "-d", str(jar)])
            item.update({"id": case_id, "artifact_created": (HERE / jar).is_file(),
                         "artifact": str(jar), "artifact_sha256": sha(HERE / jar) if (HERE / jar).is_file() else None})
            report["compiles"].append(item)
            return item
        # The representative is compiled and run once, then retained in this same attempt.
        compile_case(*compile_inputs[0])
        accepted = report["compiles"][0]
        if accepted["exit_code"] != 0 or not accepted["artifact_created"]:
            raise RuntimeError("snapshot比較のコードをcompileできない")
        classpath = os.pathsep.join([accepted["artifact"], str(compiler.parent.parent / "lib/kotlin-stdlib.jar")])
        def run_case(mode, input_name):
            item = execute(mode + "-" + input_name,
                           [str(java), "-Xmx64m", "-XX:ActiveProcessorCount=1", "-cp", classpath,
                            "SnapshotAndContrastKt", mode, input_name])
            item.update({"mode": mode, "input": input_name})
            report["runs"].append(item)
            return item
        representative = run_case("mutable-snapshot", "ada")
        fixed = next(r for r in expected["runs"] if (r["mode"], r["input"]) == ("mutable-snapshot", "ada"))
        if representative["exit_code"] != fixed["exit_code"] or representative["stdout"] != fixed["stdout"] or representative["stderr"]:
            raise RuntimeError("Representative runtime differs from fixed expectations")
        report["representative_passed"] = True
        report["collection_complete"] = False
        save_report()
        print(json.dumps({"checkpoint": "representative-passed", "compile_count": 1, "runtime_count": 1}), flush=True)
        report["resource_gate_after_representative"] = assess()
        (out / "resource-gate-after-representative.json").write_text(json.dumps(report["resource_gate_after_representative"], indent=2) + "\n")
        if not report["resource_gate_after_representative"]["allowed"]:
            raise RuntimeError("No measured headroom after representative; remaining cases were not started")
        for case_id, source in compile_inputs[1:]:
            compile_case(case_id, source)
        for fixed in expected["runs"]:
            if (fixed["mode"], fixed["input"]) != ("mutable-snapshot", "ada"):
                run_case(fixed["mode"], fixed["input"])
        report["collection_complete"] = True
    except Exception as error:
        report["errors"].append(str(error).replace(str(HERE), "<lesson>").replace(str(Path.home()), "~"))
        report["collection_complete"] = False
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        report["batch_elapsed_seconds"] = round(45 - (deadline - time.monotonic()), 6)
        report["source_unchanged"] = report["source_sha256"] == {name: sha(HERE / name) for name in names}
        save_report()
    print(json.dumps({"report": str(out.relative_to(HERE) / "run.json"),
                      "collection_complete": report["collection_complete"], "errors": report["errors"]}, ensure_ascii=False))
    return 0 if report["collection_complete"] else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--priority-child":
        # Only this newly created child lowers its own priority, then execs one command.
        before = os.getpriority(os.PRIO_PROCESS, 0)
        os.nice(10)
        after = os.getpriority(os.PRIO_PROCESS, 0)
        Path(sys.argv[2]).write_text(json.dumps({"pid": os.getpid(), "pgid": os.getpgrp(), "before": before,
                                              "after": after, "verified_before_exec": after >= 10}) + "\n")
        if after < 10:
            raise SystemExit("Unable to apply mandatory low priority")
        os.execvpe(sys.argv[3], sys.argv[3:], os.environ)
    raise SystemExit(main())

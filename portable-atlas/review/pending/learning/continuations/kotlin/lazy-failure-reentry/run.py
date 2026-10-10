#!/usr/bin/env python3
"""Atlas: one compile and one bounded JVM, with saved partial output and no automatic retry."""
import argparse
import datetime
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def group_state(pgid):
    try:
        os.killpg(pgid, 0)
        return "present"
    except ProcessLookupError:
        return "absent"
    except PermissionError:
        return "unknown-permission"

def execute(label, command, out, env, deadline, limit):
    priority_file = out / (label + ".priority.json")
    argv = [sys.executable, "-B", str(ROOT / "priority_launcher.py"), str(priority_file), "--"] + command
    record = {"label": label, "argv": argv, "target_command": command, "attempt": 1, "retry": 0,
              "timeout_seconds": limit, "timed_out": False, "cleanup": [], "priority": None,
              "target_start_confirmed": False, "target_not_started": None}
    process = None
    stdout = stderr = b""
    begin = time.monotonic()
    try:
        remaining = min(limit, deadline - begin)
        if remaining <= 0:
            raise TimeoutError("batch deadline before launcher")
        process = subprocess.Popen(argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        record["owned_pid"] = record["owned_pgid"] = process.pid
        try:
            stdout, stderr = process.communicate(timeout=remaining)
        except subprocess.TimeoutExpired as error:
            stdout, stderr = error.stdout or b"", error.stderr or b""
            record["timed_out"] = True
        record["exit_code"] = process.poll()
    except Exception as error:
        record["execution_error"] = {"type": type(error).__name__, "detail": str(error)}
    finally:
        if process is not None:
            state = group_state(process.pid)
            record["owned_group_before_cleanup"] = state
            if state != "absent" and not record["timed_out"] and not record.get("execution_error"):
                record["execution_error"] = {"type": "UnexpectedRemainingProcessGroup", "detail": state}
            if state == "present":
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    record["cleanup"].append("TERM sent only to owned process group")
                except ProcessLookupError:
                    pass
                except Exception as error:
                    record["cleanup"].append({"TERM_error": str(error)})
                stop = time.monotonic() + 0.5
                while time.monotonic() < stop and group_state(process.pid) == "present":
                    process.poll()
                    time.sleep(0.01)
                if group_state(process.pid) == "present":
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                        record["cleanup"].append("KILL sent only to owned process group")
                    except ProcessLookupError:
                        pass
                    except Exception as error:
                        record["cleanup"].append({"KILL_error": str(error)})
            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired as error:
                stdout, stderr = error.stdout or stdout, error.stderr or stderr
                record["cleanup"].append("owned process or pipes were not recovered within one second")
            except Exception as error:
                record["cleanup"].append({"communicate_error": str(error)})
            record["exit_code"] = process.poll()
            record["owned_group_after"] = group_state(process.pid)
            record["owned_process_reaped"] = process.returncode is not None
        else:
            record["target_not_started"] = True
            record["owned_group_after"] = "no-process-created"
            record["owned_process_reaped"] = True
        if priority_file.exists():
            try:
                record["priority"] = json.loads(priority_file.read_text())
                if record["priority"].get("target_started") is False:
                    record["target_not_started"] = True
            except Exception as error:
                record["execution_error"] = {"type": "PriorityRecordError", "detail": str(error)}
        for stream, data in [("stdout", stdout), ("stderr", stderr)]:
            file = out / (label + "." + stream + ".txt")
            file.write_bytes(data)
            record[stream] = {"path": str(file.relative_to(ROOT)), "bytes": len(data), "sha256": digest(file)}
        record["elapsed_seconds"] = time.monotonic() - begin
    priority_ok = record["priority"] and record["priority"]["priority"]["verified_before_exec"]
    record["success"] = bool(priority_ok and not record["timed_out"] and not record.get("execution_error")
                             and record.get("exit_code") == 0 and record["owned_process_reaped"]
                             and record["owned_group_after"] == "absent")
    return record, stdout, stderr

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--resource-record", required=True, type=Path)
    args = parser.parse_args()
    out = ROOT / "observations" / datetime.datetime.now(datetime.timezone.utc).strftime("attempt-%Y%m%dT%H%M%S%fZ")
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    report = {"project": "Atlas", "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "attempt": 1, "retry_count": 0, "commands": [], "records": [], "errors": [],
              "compile_count": 0, "jvm_count": 0, "exec_attempt_counts": {"compile": 0, "runtime": 0},
              "count_semantics": "compile_count/jvm_count count confirmed target starts; unknown starts are listed separately",
              "unconfirmed_target_starts": [], "collection_complete": False}
    inputs = ["CONTRACT.md", "expected.json", "src/LazyFailureReentry.kt", "run.py", "priority_launcher.py", "verify.py"]
    report["input_sha256"] = {n: digest(ROOT / n) for n in inputs}
    try:
        gate_file = args.resource_record.resolve()
        gate_file.relative_to(ROOT)
        gate = json.loads(gate_file.read_text())
        age = time.time() - datetime.datetime.fromisoformat(gate["observed_at_iso"]).timestamp()
        report["resource_gate"] = {"path": str(gate_file.relative_to(ROOT)), "sha256": digest(gate_file), "age_seconds": age, "record": gate}
        if not gate["allowed"] or not 0 <= age <= 120 or gate["loadavg"][0] >= 6:
            raise RuntimeError("fresh resource conditions are not satisfied; no compiler started")
        tool = json.loads((ROOT / "records/toolchain-readback.json").read_text())
        for f in tool["compiler_files"]:
            if digest(Path(f["path"])) != f["sha256"]:
                raise RuntimeError("compiler file changed: " + f["path"])
        for pathkey, hashkey in [("path", "sha256"), ("release_path", "release_sha256"), ("jvm_library_path", "jvm_library_sha256")]:
            if digest(Path(tool["java"][pathkey])) != tool["java"][hashkey]:
                raise RuntimeError("Java toolchain changed")
        report["toolchain_record_sha256"] = digest(ROOT / "records/toolchain-readback.json")
        compiler = str(Path(tool["compiler_root"]) / "bin/kotlinc")
        java = tool["java"]["path"]
        env = os.environ.copy()
        for key in ["CLASSPATH", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS", "JAVA_OPTS", "KOTLIN_OPTS"]:
            env.pop(key, None)
        env.update({"JAVACMD": java, "JAVA_OPTS": "-Xms32m -Xmx256m -XX:ActiveProcessorCount=1", "LC_ALL": "C", "LANG": "C"})
        report["explicit_environment"] = {key: env[key] for key in ["JAVACMD", "JAVA_OPTS", "LC_ALL", "LANG"]}
        artifact = out / "lesson.jar"
        command, _, _ = execute("compile", [compiler, str(ROOT / "src/LazyFailureReentry.kt"), "-jvm-target", "17", "-include-runtime", "-d", str(artifact)], out, env, start + 45, 15)
        report["commands"].append(command)
        report["exec_attempt_counts"]["compile"] = int(bool(command["priority"] and command["priority"].get("exec_attempted")))
        if artifact.is_file():
            command["target_start_confirmed"] = True
            report["compile_count"] = 1
        if not command["success"] or not artifact.is_file():
            raise RuntimeError("compile did not complete; JVM case execution not started")
        report["artifact"] = {"path": str(artifact.relative_to(ROOT)), "sha256": digest(artifact), "bytes": artifact.stat().st_size}
        command, output, _ = execute("runtime", [java, "-Xms16m", "-Xmx64m", "-XX:ActiveProcessorCount=1", "-jar", str(artifact)], out, env, start + 45, 10)
        report["commands"].append(command)
        report["exec_attempt_counts"]["runtime"] = int(bool(command["priority"] and command["priority"].get("exec_attempted")))
        for index, line in enumerate(output.splitlines(), 1):
            try:
                report["records"].append(json.loads(line))
            except Exception as error:
                report["errors"].append({"kind": "partial-or-invalid-runtime-line", "line_number": index, "line": line.decode("utf-8", "replace"), "detail": str(error)})
        if report["records"]:
            command["target_start_confirmed"] = True
            report["jvm_count"] = 1
        if not command["success"] or report["errors"]:
            raise RuntimeError("runtime incomplete; partial records retained")
        report["collection_complete"] = len([r for r in report["records"] if r.get("kind") == "case"]) == 6 and report["records"][-1].get("kind") == "batch-complete"
    except Exception as error:
        report["errors"].append({"type": type(error).__name__, "detail": str(error), "traceback": traceback.format_exc()})
    finally:
        report["unconfirmed_target_starts"] = [c["label"] for c in report["commands"]
            if not c["target_start_confirmed"] and c["target_not_started"] is not True]
        report["input_unchanged"] = all(digest(ROOT / n) == v for n, v in report["input_sha256"].items())
        report["elapsed_seconds"] = time.monotonic() - start
        report["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (out / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"run": str((out / "run.json").relative_to(ROOT)), "collection_complete": report["collection_complete"], "errors": report["errors"], "compile_count": report["compile_count"], "jvm_count": report["jvm_count"]}, ensure_ascii=False))
    return 0 if report["collection_complete"] and not report["errors"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

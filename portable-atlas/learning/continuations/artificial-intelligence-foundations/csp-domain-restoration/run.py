#!/usr/bin/env python3
"""Atlas: one bounded Python producer, with saved partial output and no automatic retry."""
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
    argv = [sys.executable, "-B", str(ROOT / "priority_launcher.py"), str(priority_file), "2", "--"] + command
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
    priority_ok = (record["priority"] and record["priority"].get("priority", {}).get("verified_before_exec")
                   and record["priority"].get("cpu_limit", {}).get("verified_before_exec"))
    record["success"] = bool(priority_ok and not record["timed_out"] and not record.get("execution_error")
                             and record.get("exit_code") == 0 and record["owned_process_reaped"]
                             and record["owned_group_after"] == "absent")
    return record, stdout, stderr


FIXED_INPUTS = ['CONTRACT.md', 'PSEUDOCODE.md', 'expected.json', 'inputs/problems.json', 'csp.py', 'producer.py',
                'run.py', 'priority_launcher.py', 'resource_parse.py', 'resource_policy.py',
                'resources.py', 'RUN_CONDITIONS.md', 'verify.py']


def check_gate_binding(gate):
    names = ['resources.py', 'resource_parse.py', 'resource_policy.py']
    if gate.get('policy_input_hashes') != {n: digest(ROOT / n) for n in names}:
        raise RuntimeError('resource policy source mismatch; target not started')
    reference = ROOT / 'records/root-browser-reference.json'
    if gate.get('root_browser_reference_sha256') != digest(reference) or gate.get('root_browser_reference') != json.loads(reference.read_text()):
        raise RuntimeError('root ownership reference mismatch; target not started')
    decision = gate.get('root_batch_decision_file') or {}
    path = Path(decision.get('path', ''))
    if not path.is_file() or digest(path) != decision.get('sha256') or json.loads(path.read_text()) != gate.get('root_batch_decision'):
        raise RuntimeError('current batch decision mismatch; target not started')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true', required=True)
    parser.add_argument('--resource-record', type=Path, required=True)
    args = parser.parse_args()
    out = ROOT / 'observations' / datetime.datetime.now(datetime.timezone.utc).strftime('attempt-%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    report = {'project': 'Atlas', 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'input_sha256': {}, 'commands': [], 'records': [], 'errors': [], 'target_count': 0,
              'exec_attempt_count': 0, 'target_retry': 0, 'collection_complete': False}
    try:
        report['input_sha256'] = {n: digest(ROOT / n) for n in FIXED_INPUTS}
        gate_file = args.resource_record.resolve()
        gate_file.relative_to(ROOT)
        gate = json.loads(gate_file.read_text())
        age = time.time() - datetime.datetime.fromisoformat(gate['observed_at_iso']).timestamp()
        report['resource_gate'] = {'path': str(gate_file.relative_to(ROOT)), 'sha256': digest(gate_file),
                                   'age_seconds': age, 'record': gate}
        check_gate_binding(gate)
        from resource_policy import evaluate
        decision = evaluate(gate)
        report['resource_gate']['recomputed_decision'] = decision
        if gate.get('allowed') is not True or not decision['allowed'] or not 0 <= age <= 60:
            raise RuntimeError('fresh resource gate not satisfied; target not started')
        env = os.environ.copy()
        env.update({'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONHASHSEED': '0', 'LC_ALL': 'C', 'LANG': 'C'})
        for key in ['PYTHONPATH', 'PYTHONHOME']:
            env.pop(key, None)
        report['explicit_environment'] = {key: env[key] for key in ['PYTHONDONTWRITEBYTECODE', 'PYTHONHASHSEED', 'LC_ALL', 'LANG']}
        report['python'] = {'path': sys.executable, 'version': sys.version, 'sha256': digest(Path(sys.executable))}
        command, output, _ = execute('producer', [sys.executable, '-B', str(ROOT / 'producer.py')], out, env, start + 10, 3)
        report['commands'].append(command)
        report['exec_attempt_count'] = int(bool(command['priority'] and command['priority'].get('exec_attempted')))
        for number, line in enumerate(output.splitlines(), 1):
            try:
                report['records'].append(json.loads(line))
            except Exception as error:
                report['errors'].append({'type': 'incomplete-or-invalid-line', 'number': number,
                                         'text': line.decode('utf-8', 'replace'), 'detail': str(error)})
        if report['records'] and report['records'][0].get('kind') == 'producer-started':
            command['target_start_confirmed'] = True
            report['target_count'] = 1
        report['collection_complete'] = bool(command['success'] and not report['errors']
            and len(report['records']) == 12 and report['records'][-1] == {
                'kind': 'batch-complete', 'case_count': 9, 'retry': 0})
        if not report['collection_complete']:
            raise RuntimeError('producer incomplete; partial output retained')
    except Exception as error:
        report['errors'].append({'type': type(error).__name__, 'detail': str(error), 'traceback': traceback.format_exc()})
    finally:
        report['input_unchanged'] = bool(report['input_sha256']) and all((ROOT / n).is_file() and digest(ROOT / n) == h for n, h in report['input_sha256'].items())
        report['target_start_unknown'] = [c['label'] for c in report['commands'] if not c['target_start_confirmed'] and c['target_not_started'] is not True]
        report['elapsed_seconds'] = time.monotonic() - start
        report['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'path': str((out / 'run.json').relative_to(ROOT)), 'complete': report['collection_complete'],
                          'target_count': report['target_count'], 'errors': report['errors']}, ensure_ascii=False))
    return 0 if report['collection_complete'] and report['input_unchanged'] and not report['errors'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

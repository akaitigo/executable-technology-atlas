"""Bounded delivery model driving actual SQLite consumer subprocesses."""
import hashlib
import json
import os
import platform
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from consumer import canonical, init_db

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.write_bytes(canonical(value))


def snapshot(path):
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        return {"balance": db.execute("SELECT balance FROM account WHERE id='demo'").fetchone()[0],
                "effects": [{"sequence": r[0], "event_id": r[1], "delta": r[2]} for r in db.execute("SELECT sequence,event_id,delta FROM effects ORDER BY sequence")],
                "inbox": [{"event_id": r[0], "fingerprint": r[1], "payload": json.loads(r[2])} for r in db.execute("SELECT event_id,fingerprint,payload FROM inbox ORDER BY event_id")]}


def msg(ident="event-a", delta=7):
    return {"id": ident, "payload": {"account": "demo", "delta": delta}}


def cases():
    def row(ident, policy="inbox", messages=None, limit=3, fault="none"):
        return {"id": ident, "policy": policy, "messages": [msg()] if messages is None else messages, "max_deliveries": limit, "fault": fault}
    return [row("normal"), row("naive-crash", "naive", fault="crash-first"), row("inbox-crash", fault="crash-first"),
            row("same-id-replay", messages=[msg(), msg()]), row("same-id-conflict", messages=[msg(), msg(delta=9)]),
            row("distinct-id", messages=[msg(), msg("event-b")]), row("poison-3", messages=[msg(delta="oops")]),
            row("poison-1", messages=[msg(delta="oops")], limit=1), row("transient-success", fault="rollback-first-two"),
            row("transient-exhausted", limit=2, fault="rollback-always"), row("invalid-limit-zero", limit=0),
            row("invalid-limit-bool", limit=True), row("invalid-id", messages=[msg("../outside")]), row("zero-delta", messages=[msg(delta=0)])]


def input_reason(inp):
    if type(inp["max_deliveries"]) is not int or not 1 <= inp["max_deliveries"] <= 3:
        return "invalid-max-deliveries"
    if type(inp["messages"]) is not list or not 1 <= len(inp["messages"]) <= 2:
        return "invalid-message-list"
    for message in inp["messages"]:
        if type(message) is not dict or set(message) != {"id", "payload"} or type(message["id"]) is not str or not re.fullmatch(r"event-[a-z]", message["id"]):
            return "invalid-event-identity"
    return None


def execute(folder, inp):
    database = folder / "consumer.sqlite"
    init_db(database)
    write(folder / "before-state.json", snapshot(database))
    reason = input_reason(inp)
    events, records, acknowledgements, dlq = [], [], [], []
    retries = 0
    if reason:
        events.append({"event": "input-blocked", "reason": reason, "at": now()})
    else:
        for message_index, message in enumerate(inp["messages"]):
            for attempt in range(1, inp["max_deliveries"] + 1):
                delivery = len(records) + 1
                if inp["fault"] == "crash-first" and message_index == 0 and attempt == 1:
                    fault = "crash-after-commit"
                elif inp["fault"] == "rollback-always" or (inp["fault"] == "rollback-first-two" and attempt <= 2):
                    fault = "rollback-before-commit"
                else:
                    fault = "none"
                request = {"message": message, "policy": inp["policy"], "fault": fault}
                request_name = "delivery-%02d-input.json" % delivery
                write(folder / request_name, request)
                actual = json.loads((folder / request_name).read_bytes())
                db_before = snapshot(database)
                db_pre_hash = sha(database.read_bytes())
                events.append({"event": "model-deliver", "delivery": delivery, "message_index": message_index, "event_id": message["id"], "attempt": attempt, "redelivered": attempt > 1, "at": now()})
                start = now()
                db_relative = database.relative_to(ROOT).as_posix()
                run = subprocess.run([sys.executable, "consumer.py", "--db", db_relative], input=json.dumps(actual),
                                     cwd=ROOT, capture_output=True, text=True, timeout=5, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                stderr = run.stderr.replace(str(ROOT), "<module>")
                stderr = re.sub(r'File "[^"\n]*/([^/"\n]+)"', r'File "<runtime>/\1"', stderr)
                trace = [json.loads(line) for line in run.stdout.splitlines() if line.strip()]
                record = {"delivery": delivery, "message_index": message_index, "attempt": attempt, "request": actual,
                          "command": ["python3", "consumer.py", "--db", db_relative], "stdin_digest": sha(json.dumps(actual).encode()),
                          "started_at": start, "completed_at": now(), "exit_code": run.returncode, "stdout": run.stdout, "stderr": stderr,
                          "stdout_digest": sha(run.stdout.encode()), "stderr_digest": sha(stderr.encode()), "trace": trace,
                          "db_before": db_before, "db_after": snapshot(database), "db_pre_digest": db_pre_hash, "db_post_digest": sha(database.read_bytes())}
                write(folder / ("delivery-%02d-command.json" % delivery), record)
                records.append(record)
                events.extend({**event, "delivery": delivery} for event in trace)
                if run.returncode == 0:
                    if not trace or trace[-1]["event"] != "ack-eligible":
                        raise ValueError("consumer exit0 without ack eligibility")
                    acknowledgements.append({"delivery": delivery, "event_id": message["id"], "message_index": message_index})
                    events.append({"event": "model-ack", "delivery": delivery, "at": now()})
                    break
                if run.returncode not in (65, 66, 70, 75):
                    raise RuntimeError("unexpected consumer exit: " + str(run.returncode) + " " + stderr)
                if run.returncode == 66 or attempt == inp["max_deliveries"]:
                    dlq.append({"message": message, "message_index": message_index, "delivery": delivery, "attempts": attempt,
                                "reason": "identity-conflict" if run.returncode == 66 else "max-deliveries-exhausted", "last_exit": run.returncode})
                    events.append({"event": "model-dlq", "delivery": delivery, "reason": dlq[-1]["reason"], "at": now()})
                    break
                retries += 1
                events.append({"event": "model-requeue", "delivery": delivery, "next_attempt": attempt + 1, "at": now()})
    after = snapshot(database)
    result = {"outcome": "blocked" if reason else "dlq" if dlq else "acknowledged", "reason": reason,
              "state": after, "deliveries": len(records), "model_retries": retries, "acknowledgements": acknowledgements, "dlq": dlq, "events": events}
    write(folder / "after-state.json", after)
    write(folder / "result.json", result)
    write(folder / "delivery-records.json", records)
    write(folder / "events.json", events)
    return result


def main(token):
    if not re.fullmatch(r"[0-9TZ]+-events", token):
        raise ValueError("invalid run token")
    started = now()
    folder = ROOT / "observations" / token
    folder.mkdir(parents=True, exist_ok=False)
    rows = []
    for inp in cases():
        case_folder = folder / inp["id"]
        case_folder.mkdir()
        write(case_folder / "input.json", inp)
        actual = json.loads((case_folder / "input.json").read_bytes())
        rows.append({"id": actual["id"], "input": actual, "result": execute(case_folder, actual), "observed_at": now()})
        assert json.loads((case_folder / "input.json").read_bytes()) == inp
    obs = {"schema_version": 1, "field_id": "messaging-event-driven-systems", "lesson_id": "sqlite-inbox-ack-window", "execution_id": token,
           "started_at": started, "completed_at": now(), "runtime": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
           "os": platform.system(), "release": platform.release(), "machine": platform.machine()}, "attempts": 1, "outer_retries": 0,
           "real_broker_executed": False, "external_effects": 0, "subject_complete": False,
           "source_bindings": {f: sha((ROOT / f).read_bytes()) for f in ("consumer.py", "experiment.py")}, "scenarios": rows}
    write(folder / "observation.json", obs)
    print(json.dumps(obs, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1])

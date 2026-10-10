"""Finite CSV data pipeline. Immutable generations + atomic current pointer."""
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

HEADER = ["id", "quantity", "price_cents", "total_cents"]
SCHEMA = {"version": 1, "columns": [["id", "string"], ["quantity", "integer"], ["price_cents", "integer"], ["total_cents", "integer"]]}


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def emit(event, **fields):
    print(json.dumps({"event": event, **fields}, ensure_ascii=False), flush=True)


def execute(publication, request):
    stage = None
    pointer_tmp = None
    try:
        if request.get("mode") not in ("replace", "append") or request.get("bad_rows") not in ("quarantine", "silent-skip") or request.get("inject") not in ("none", "transform", "before-publish"):
            raise ValueError("unsupported-config")
        source = request["csv"]
        reader = csv.reader(io.StringIO(source, newline=""), strict=True)
        if next(reader, None) != ["id", "quantity", "price"]:
            raise ValueError("source-schema-mismatch")
        records = [(i, reader.line_num, row) for i, row in enumerate(reader, 1)]
        emit("ingested", input_count=len(records), input_digest=sha(source.encode()))
        if request["inject"] == "transform":
            raise RuntimeError("injected-transform-stage")
        seen, lineage, quarantined = {}, [], []
        duplicates = 0
        for number, end_line, raw in records:
            reason = None
            typed = None
            if len(raw) != 3 or not raw[0].strip():
                reason = "shape-or-id"
            elif not re.fullmatch(r"[1-9][0-9]*", raw[1]) or not 1 <= int(raw[1]) <= 100:
                reason = "quantity"
            elif not re.fullmatch(r"(?:0|[1-9][0-9]*)\.[0-9]{2}", raw[2]) or Decimal(raw[2]) > 100000:
                reason = "price"
            else:
                cents = int(Decimal(raw[2]) * 100)
                typed = [raw[0].strip(), int(raw[1]), cents, int(raw[1]) * cents]
                if typed[0] in seen and seen[typed[0]] != typed:
                    reason = "conflicting-id"
            origin = {"record": number, "end_line": end_line, "raw": raw}
            if reason:
                if request["bad_rows"] == "quarantine":
                    quarantined.append({**origin, "reason": reason})
                    lineage.append({**origin, "disposition": "quarantined"})
                    emit("quarantined", **origin, reason=reason)
                else:
                    # Bad policy: source record disappears from published quarantine/lineage.
                    emit("silent-skip", **origin, reason=reason)
                continue
            if typed[0] in seen:
                duplicates += 1
                lineage.append({**origin, "disposition": "duplicate", "typed": typed})
                emit("duplicate-dropped", **origin)
            else:
                seen[typed[0]] = typed
                lineage.append({**origin, "disposition": "accepted", "typed": typed})
                emit("typed", **origin, row=typed)
        batch = [seen[key] for key in sorted(seen)]
        output = batch
        if request["mode"] == "append" and (publication / "current.json").exists():
            prior = json.loads((publication / "current.json").read_text())["generation"]
            with (publication / "generations" / prior / "output.csv").open(newline="") as f:
                previous = list(csv.reader(f))[1:]
            output = [[r[0], *map(int, r[1:])] for r in previous] + batch
            emit("append-previous-output", prior_rows=len(previous))
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(output)
        counts = {"input": len(records), "accepted": len(batch), "duplicates": duplicates, "quarantined": len(quarantined)}
        payloads = {"output.csv": stream.getvalue().encode(), "quarantine.json": encoded(quarantined), "schema.json": encoded(SCHEMA), "lineage.json": encoded({"input_digest": sha(source.encode()), "producer_digest": sha(Path(__file__).read_bytes()), "records": lineage, "counts": counts, "mode": request["mode"], "bad_rows": request["bad_rows"]})}
        manifest = {name: {"digest": sha(raw), "size": len(raw)} for name, raw in payloads.items()}
        payloads["manifest.json"] = encoded(manifest)
        generation = hashlib.sha256(encoded(manifest)).hexdigest()
        publication.mkdir(parents=True, exist_ok=True)
        generations = publication / "generations"
        generations.mkdir(exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".stage-", dir=publication))
        for name, raw in payloads.items():
            (stage / name).write_bytes(raw)
        emit("staged", output_rows=len(output), generation=generation, counts=counts)
        if request["inject"] == "before-publish":
            raise RuntimeError("injected-before-publish")
        target = generations / generation
        if target.exists():
            if any((target / name).read_bytes() != raw for name, raw in payloads.items()):
                raise ValueError("generation-content-conflict")
            shutil.rmtree(stage)
        else:
            os.replace(stage, target)
        stage = None
        fd, temp_name = tempfile.mkstemp(prefix=".pointer-", dir=publication)
        pointer_tmp = Path(temp_name)
        with os.fdopen(fd, "wb") as f:
            f.write(encoded({"generation": generation}))
        os.replace(pointer_tmp, publication / "current.json")
        pointer_tmp = None
        emit("published", generation=generation, output_rows=len(output), counts=counts)
        return 0
    except (ValueError, csv.Error) as exc:
        emit("refused", reason=str(exc))
        return 2
    except RuntimeError as exc:
        emit("stage-failed", reason=str(exc))
        return 3
    finally:
        if stage is not None and stage.exists():
            shutil.rmtree(stage)
        if pointer_tmp is not None and pointer_tmp.exists():
            pointer_tmp.unlink()
        emit("cleanup", temporary_staging_removed=True)


if __name__ == "__main__":
    raise SystemExit(execute(Path(sys.argv[1]), json.load(sys.stdin)))

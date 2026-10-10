"""Read-only checks: independent enumeration, hand trace, boundaries, provenance."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import subprocess
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from cache import CASES, analyze, config, simulate

ROOT = Path(__file__).resolve().parent


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def fingerprint():
    return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in ROOT.rglob("*") if p.is_file()}


def enumeration(spec, broken=False):
    """No production mapping/memory functions: enumerate address ranges and slots."""
    width = spec["line_bytes"]
    slots = len(list(range(0, spec["capacity_bytes"], width)))
    values, byte = [], 3
    for _ in range(256):
        values.append(byte)
        byte += 17
        if byte >= 256:
            byte -= 256
    mapping, slot, tag, block = [], 0, 0, 0
    for base in range(0, 256, width):
        mapping.append((base, base + width, block, slot, tag))
        block += 1
        slot += 1
        if slot == slots:
            slot = 0
            tag += 1
    resident = [None] * slots
    seen, events = set(), []

    def snapshot():
        return [{"valid": item is not None,
                 "tag": item[4] if item else None,
                 "block": item[2] if item else None,
                 "bytes": values[item[0]:item[1]] if item else []} for item in resident]

    initial = snapshot()
    hits = misses = evictions = wrong = 0
    for position, address in enumerate(spec["addresses"]):
        requested = next(item for item in mapping if address in range(item[0], item[1]))
        base, end, block, index, tag = requested
        offset = list(range(base, end)).index(address)
        before = snapshot()
        old = resident[index]
        match = old is not None and old[4] == tag
        hit = old is not None and (match or broken)
        evicted = old[2] if old is not None and not hit else None
        if hit:
            hits += 1
        else:
            misses += 1
            evictions += int(evicted is not None)
            resident[index] = requested
        observed = values[resident[index][0] + offset]
        correct = observed == values[address]
        wrong += int(not correct)
        events.append({"step": position + 1, "address": address, "block": block, "index": index,
                       "tag": tag, "offset": offset, "requested_range": [base, end - 1],
                       "before": before, "after": snapshot(), "tag_match": match, "hit": hit,
                       "decision_reason": "valid-and-tag-match" if match else "invalid-line" if old is None else "tag-mismatch",
                       "tag_check_bypassed": broken and old is not None and not match,
                       "seen_block_before": block in seen, "evicted_block": evicted,
                       "empty_lines_before": before.count({"valid": False, "tag": None, "block": None, "bytes": []}),
                       "memory_bytes_fetched": 0 if hit else width,
                       "expected_byte": values[address], "observed_byte": observed, "data_correct": correct})
        seen.add(block)
    def bits(value):
        n, power = 0, 1
        while power < value:
            power *= 2
            n += 1
        return n
    return {"policy": "broken-ignore-tag" if broken else "valid-and-tag",
            "geometry": {"line_count": slots, "offset_bits": bits(width), "index_bits": bits(slots),
                         "tag_bits": 8 - bits(width) - bits(slots)},
            "initial_lines": initial, "trace": events, "final_lines": snapshot(),
            "summary": {"reads": len(events), "hits": hits, "misses": misses, "evictions": evictions,
                        "wrong_bytes": wrong, "hit_rate": hits / len(events) if events else None,
                        "memory_bytes_fetched": misses * width}}


def check_case(case, spec):
    assert case["input"] == spec, "input drift"
    rejected = {"invalid_capacity": "capacity_bytes", "invalid_line": "line_bytes",
                "line_exceeds_capacity": "line_bytes", "invalid_address": "addresses[1]"}
    case_name = next((key for key in rejected if spec == CASES[key]), None)
    if case_name:
        assert case["status"] == "rejected" and case["error"]["field"] == rejected[case_name]
        assert case["normal"] is None and case["broken"] is None and case["trace"] == []
    else:
        assert case["status"] == "passed" and case["error"] is None
        assert case["normal"] == enumeration(spec), "normal trace/snapshot/data mismatch"
        assert case["broken"] == enumeration(spec, True), "broken variant drift"


def check_record(record):
    assert record["attempts"] == 1 and record["retries"] == 0 and record["exit_code"] == 0
    assert record["classification"] == "actual-Python-logical-simulator-run-not-CPU-measurement"
    assert record["started_at"] <= record["finished_at"] and record["started_at"].endswith("+09:00")
    assert set(record["environment"]) == {"python", "implementation", "os", "release", "architecture"}
    assert record["command"] == "python3 -B check.py"
    assert record["publish_command"] == "python3 -B observe.py --write-evidence"
    assert record["input"] == CASES
    assert set(record["source_hashes"]) == {"cache.py", "check.py", "observe.py", "verify.py", "sources.json"}
    for name, expected in record["source_hashes"].items():
        assert digest((ROOT / name).read_bytes()) == expected, "source digest mismatch: " + name
    for item in [record["raw_stdout"], record["raw_stderr"]] + record["artifacts"]:
        assert digest((ROOT / item["path"]).read_bytes()) == item["digest"], "artifact digest mismatch"
    assert record["raw_stdout"]["path"] == "evidence/stdout.json"
    assert record["raw_stderr"]["path"] == "evidence/stderr.txt"
    assert (ROOT / "evidence/stderr.txt").read_bytes() == b""
    assert record["artifacts"][0]["classification"] == "actual-logical-trace-redraw-not-screenshot"
    assert record["source_version"] == record["result"]["model_version"] == "bounded-direct-mapped-read-v1"
    result = record["result"]
    assert json.loads((ROOT / "evidence/stdout.json").read_bytes()) == result
    assert result["classification"] == "logical-simulator-not-CPU-cache-measurement"
    assert result["limits"] == {"address_bits": 8, "capacity_max": 64, "line_max": 16, "reads_max": 64}
    assert set(result["cases"]) == set(CASES)
    for name, spec in CASES.items():
        check_case(result["cases"][name], spec)


def check_learning_links():
    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links, self.ids = [], set()
        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            if "id" in values:
                self.ids.add(values["id"])
            if tag == "a" and "href" in values:
                self.links.append(values["href"])
            if tag in ["script", "link"]:
                self.links.append(values.get("src", values.get("href", "")))
    html = (ROOT / "index.html").read_text()
    page = Links(); page.feed(html)
    readme = (ROOT / "README.md").read_text()
    markdown_links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme)
    checked = 0
    for links in [page.links, markdown_links]:
        for link in links:
            parsed = urlsplit(link)
            if parsed.scheme:
                assert parsed.scheme in ["https", "data"]
                continue
            path = unquote(parsed.path)
            if path:
                assert (ROOT / path).resolve().is_relative_to(ROOT)
                assert (ROOT / path).is_file(), "missing local link: " + link
                checked += 1
            elif parsed.fragment:
                assert unquote(parsed.fragment) in page.ids or parsed.fragment == "検査と根拠"
    supported = json.loads((ROOT / "sources.json").read_text())["sources"]
    external = {urlsplit(url)._replace(fragment="").geturl() for url in page.links if url.startswith("https:")}
    assert {item["url"] for item in supported}.issubset(external)
    roadmap_sources = {
        "https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/caches.html#larger-blocks",
        "https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/caches.html#handling-stores",
        "https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/pipelining.html#hazards",
        "https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html",
        "https://docs.riscv.org/reference/isa/v20260120/unpriv/rvwmo.html"
    }
    assert roadmap_sources.issubset(set(page.links)) and roadmap_sources.issubset(set(markdown_links))
    assert "cache-roadmap" in page.ids and "data-field-id=\"computer-architecture-digital-systems\"" in html
    return checked


def main():
    before = fingerprint()
    record = json.loads((ROOT / "evidence/run.json").read_bytes())
    check_record(record)
    ui_data = (ROOT / "data.js").read_text()
    assert ui_data.startswith("window.CACHE_OBSERVATION = ") and ui_data.endswith(";\n")
    assert json.loads(ui_data[len("window.CACHE_OBSERVATION = "):-2]) == record
    cases = record["result"]["cases"]
    expected = {"conflict": (0, 4, 3, 3, 1, 0, 2), "spatial": (5, 3, 0, 5, 3, 0, 0),
                "offset_conflict": (3, 3, 2, 5, 1, 0, 2), "one_line": (1, 3, 2, 3, 1, 0, 2),
                "upper_boundary": (4, 4, 1, 5, 3, 0, 2), "empty": (0, 0, 0, 0, 0, 0, 0)}
    for name, hand in expected.items():
        normal, broken = cases[name]["normal"]["summary"], cases[name]["broken"]["summary"]
        observed = tuple(normal[k] for k in ["hits", "misses", "evictions"]) + tuple(broken[k] for k in ["hits", "misses", "evictions", "wrong_bytes"])
        assert observed == hand, (name, observed, hand)
    main_events = cases["conflict"]["normal"]["trace"]
    assert [(e["address"], e["block"], e["index"], e["tag"], e["offset"], e["hit"], e["evicted_block"], e["observed_byte"]) for e in main_events] == [
        (0, 0, 0, 0, 0, False, None, 3), (16, 4, 0, 1, 0, False, 0, 19),
        (0, 0, 0, 0, 0, False, 4, 3), (16, 4, 0, 1, 0, False, 0, 19)]
    assert all(e["empty_lines_before"] == 3 for e in main_events[1:])
    assert main_events[1]["seen_block_before"] is False and main_events[2]["seen_block_before"] is True
    assert cases["empty"]["normal"]["summary"]["hit_rate"] is None
    geometries = [(c, b) for c in [1, 2, 4, 8, 16, 32, 64] for b in [1, 2, 4, 8, 16] if b <= c]
    mappings = 0
    for capacity, width in geometries:
        for address in range(256):
            spec = config(capacity, width, [address])
            assert simulate(spec) == enumeration(spec)
            mappings += 1
    exhaustive = 0
    for addresses in itertools.product([0, 1, 16, 17], repeat=4):
        spec = config(addresses=list(addresses))
        assert simulate(spec) == enumeration(spec)
        assert simulate(spec, True) == enumeration(spec, True)
        exhaustive += 1
    rng = random.Random(3410)
    for _ in range(200):
        c, b = rng.choice(geometries)
        spec = config(c, b, [rng.randrange(256) for _ in range(rng.randrange(1, 33))])
        assert simulate(spec) == enumeration(spec)
        assert simulate(spec, True) == enumeration(spec, True)
    invalid = [config(0, 1), config(-1, 1), config(128, 1), config(True, 1), config(12, 4),
               config(16, 0), config(16, 3), config(64, 32), config(4, 8), config(addresses=[-1]),
               config(addresses=[256]), config(addresses=[True]), config(addresses=[1.5]),
               config(addresses="0"), config(addresses=[0] * 65), None, {},
               {**config(), "address_bits": 16}, {**config(), "store": 0}]
    for spec in invalid:
        answer = analyze(spec)
        assert answer["status"] == "rejected" and answer["normal"] is None and answer["trace"] == []
    assert simulate(config(addresses=[0] * 64))["summary"]["hits"] == 63
    mutations = []
    for field, value in [("hit", True), ("tag", 5), ("evicted_block", 99), ("observed_byte", 0)]:
        bad = copy.deepcopy(record)
        bad["result"]["cases"]["conflict"]["normal"]["trace"][1][field] = value
        mutations.append(bad)
    bad = copy.deepcopy(record); bad["raw_stdout"]["digest"] = "sha256:bad"; mutations.append(bad)
    bad = copy.deepcopy(record); bad["source_hashes"]["cache.py"] = "sha256:bad"; mutations.append(bad)
    bad = copy.deepcopy(record); bad["input"]["conflict"]["addresses"] = [0]; mutations.append(bad)
    bad = copy.deepcopy(record); bad["result"]["cases"]["invalid_address"]["normal"] = {}; mutations.append(bad)
    for bad in mutations:
        try:
            check_record(bad)
        except AssertionError:
            pass
        else:
            raise AssertionError("tampered evidence accepted")
    # Check case-specific mutations independently too; raw equality must not mask oracle defects.
    for field, value in [("hit", True), ("tag", 5), ("evicted_block", 99), ("observed_byte", 0)]:
        bad = copy.deepcopy(cases["conflict"])
        bad["normal"]["trace"][1][field] = value
        try:
            check_case(bad, CASES["conflict"])
        except AssertionError:
            pass
        else:
            raise AssertionError("oracle accepted mutated trace")
    for script in ["check.py", "observe.py"]:
        completed = subprocess.run([sys.executable, "-B", script], cwd=ROOT, capture_output=True, timeout=10)
        assert completed.returncode == 0 and completed.stderr == b""
        assert completed.stdout == (ROOT / "evidence/stdout.json").read_bytes()
    completed = subprocess.run([sys.executable, "-B", "check.py", "--input-json", json.dumps(config(12, 4))], cwd=ROOT, capture_output=True, timeout=10)
    assert completed.returncode == 2 and json.loads(completed.stdout)["error"]["field"] == "capacity_bytes"
    links = check_learning_links()
    assert fingerprint() == before, "read-only contract broken"
    print("PASS: hand trace + independent enumeration; geometries=%d mappings=%d exhaustive-traces=%d generated=200 invalid=%d record-negative=%d oracle-negative=4 read-only=3 local-links=%d roadmap/source-binding" % (len(geometries), mappings, exhaustive, len(invalid), len(mutations), links))


if __name__ == "__main__":
    main()

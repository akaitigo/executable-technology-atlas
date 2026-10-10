#!/usr/bin/env python3
"""実装前の手計算表で固定6順序を照合する。--record以外はファイルを変更しない。"""
import argparse
import copy
import datetime
import hashlib
import itertools
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
from html.parser import HTMLParser
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
from model import schedule

ROOT = Path(__file__).resolve().parent
BOUND = ("hand-oracle.json", "hand-oracle-lock.json", "model.py", "app.js", "index.html",
         "check-js.cjs", "checker.py", "README.md", "COVERAGE.md", "sources.json",
         "skills/atlas-capacity-priority/SKILL.md")


def check_result(actual, expected):
    assert actual["order"] == expected["order"]
    assert set(actual["jobs"]) == {"A", "B", "C"}
    for i, name in enumerate("ABC"):
        assert actual["jobs"][name] == {"arrival": 0, "service": 5 if name == "A" else 1,
            "start": expected["start_by_ABC"][i], "finish": expected["finish_by_ABC"][i],
            "wait": expected["start_by_ABC"][i], "response": expected["finish_by_ABC"][i]}
    for key in ("sum_completion", "mean_completion", "mean_wait", "max_completion", "makespan", "throughput"):
        assert actual[key] == expected[key], (key, actual[key], expected[key])
    assert actual["benchmark"] is False
    assert actual["time_unit"] == "model tick"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.links.append(attrs[key])


def collect():
    hand = json.loads((ROOT / "hand-oracle.json").read_text())
    lock = json.loads((ROOT / "hand-oracle-lock.json").read_text())
    assert hashlib.sha256((ROOT / "hand-oracle.json").read_bytes()).hexdigest() == lock["sha256"]
    assert all(exists is False for _, exists in lock["implementation_files_exist"])
    assert sorted(row["order"] for row in hand["cases"]) == sorted("".join(p) for p in itertools.permutations("ABC"))
    rows = []
    for expected in hand["cases"]:
        actual = schedule(expected["order"])
        check_result(actual, expected)
        rows.append(actual)
    refused = []
    for value in (None, False, 0, [], {}, "", "AB", "ABA", "ABCD", "abc"):
        try:
            schedule(value)
        except ValueError as error:
            assert str(error).startswith("REFUSED_INPUT:")
            refused.append({"input": value, "outcome": "expected_refusal", "diagnostic": str(error)})
        else:
            raise AssertionError(("invalid_input_accepted", value))
    alterations = []
    for name, change in (
        ("Aの完了を5と偽る", lambda r: r["jobs"]["A"].update(finish=5)),
        ("平均完了を平均待ちと混同する", lambda r: r.update(mean_completion="1")),
        ("短い順で処理能力が増えたと偽る", lambda r: r.update(makespan=5, throughput="3/5")),
    ):
        mutated = copy.deepcopy(rows[3])
        change(mutated)
        try:
            check_result(mutated, hand["cases"][3])
        except AssertionError:
            alterations.append({"alteration": name, "detected": True})
        else:
            raise AssertionError(("alteration_undetected", name))
    node = subprocess.run(["node", "check-js.cjs"], cwd=ROOT, capture_output=True, text=True, timeout=5)
    assert node.returncode == 0, node.stderr
    javascript = json.loads(node.stdout)
    assert javascript["passed"] is True
    assert [case["result"] for case in javascript["cases"]] == rows
    page = Page()
    page.feed((ROOT / "index.html").read_text())
    assert len(page.ids) == len(set(page.ids)), "duplicate_html_id"
    local_links = []
    for link in page.links:
        url = urlsplit(link)
        if not url.scheme and url.path:
            # 原票は--recordが作る。存在確認はmainで保存後にも行う。
            if url.path != "observations/run.json":
                assert (ROOT / url.path).is_file(), ("missing_local_link", link)
            local_links.append(url.path)
    return {"python_cases": rows, "expected_refusals": refused,
            "altered_result_detection": alterations, "javascript": javascript,
            "html_static": {"duplicate_ids": False, "local_links": local_links,
                            "browser_rendering_tested": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true", help="このstagingの実行観測を保存する")
    args = parser.parse_args()
    start = time.perf_counter()
    payload = collect()
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in BOUND}
    path = ROOT / "observations/run.json"
    if args.record:
        path.parent.mkdir(exist_ok=True)
        node_version = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        node_version.check_returncode()
        record = {"recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "attempt": 1, "retry": 0, "passed": True,
                  "environment": {"python": platform.python_version(), "node": node_version.stdout.strip(),
                                  "system": platform.system(), "release": platform.release(), "machine": platform.machine()},
                  "elapsed_seconds": round(time.perf_counter() - start, 6),
                  "elapsed_is_benchmark": False, "source_sha256": hashes, "results": payload,
                  "visual_qa": {"status": "未実施", "reason": "実ブラウザ操作ツールが提供されていないため。", "capture_files": [],
                                "dom_events_tested": False, "screenshots_reconstructed": False},
                  "integration": {"status": "独立staging。受入・Portal統合は未実施。", "accepted_count_increment": 0}}
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    else:
        saved = json.loads(path.read_text())
        # 後日のUI/文書修正は別manifestへ結ぶ。旧実行原票を現hashで上書きしない。
        manifest_path = ROOT / "observations/current-source-manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text())
            assert manifest["saved_run_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
            assert manifest["derived_manifest"] is True
            assert manifest["source_sha256"] == hashes, "source_changed_after_manifest"
            assert manifest["html_static"] == payload["html_static"], "html_changed_after_manifest"
            assert {k: v for k, v in saved["results"].items() if k != "html_static"} == {
                k: v for k, v in payload.items() if k != "html_static"}, "numerical_result_changed"
        else:
            assert saved["source_sha256"] == hashes, "source_changed_after_record"
            assert saved["results"] == payload, "result_changed_after_record"
    assert path.is_file()
    print(json.dumps({"passed": True, "python_orders": 6, "javascript_orders": 6, "frames": 48,
                      "python_expected_refusals": 10, "javascript_expected_refusals": 16,
                      "altered_results_detected": 3, "state_transition_checks": 5,
                      "visual_qa": "このコマンドは数値検査のみ。別実行のブラウザ確認はREADMEを参照。", "recorded": args.record}, ensure_ascii=False))


if __name__ == "__main__":
    main()

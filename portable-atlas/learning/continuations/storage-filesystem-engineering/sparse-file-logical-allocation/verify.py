#!/usr/bin/env python3
"""実験を再実行せず、固定期待値と圧縮保存した実読取りバイトを照合する。"""
import base64
import hashlib
import json
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check(observation):
    expected_bytes = (HERE / "expected.json").read_bytes()
    expected = json.loads(expected_bytes)
    checks = []

    def same(label, actual, wanted):
        if type(actual) is not type(wanted) or actual != wanted:
            raise AssertionError(label + ": 期待値と不一致")
        checks.append(label)

    same("観測形式", observation["schema"], "atlas.sparse-file.observation.v1")
    same("固定期待値の結合", observation["source_bindings"]["expected.json"], hashlib.sha256(expected_bytes).hexdigest())
    same("実行ソースの結合", observation["source_bindings"]["experiment.py"], hashlib.sha256((HERE / "experiment.py").read_bytes()).hexdigest())
    same("作成ファイル数・上限", observation["limits"], {"files": 2, "max_file_bytes": 65536, "external_path_input": False})
    for key in ("offset", "read_at_zero_hex", "read_at_cursor_hex"):
        same("seekのみ: " + key, observation["seek_only"][key], expected["seek_only"][key])
    same("seekのみ: 論理長", observation["seek_only"]["stat"]["logical_bytes"], expected["seek_only"]["logical_size"])
    full_contents = []
    for name in ("sparse_written", "dense_written"):
        actual, fixed = observation[name], expected[name]
        same(name + ": 論理長", actual["stat"]["logical_bytes"], fixed["logical_size"])
        same(name + ": 書込量", sum(actual["write_returns"]), fixed["write_bytes"])
        same(name + ": 書込後の位置", actual["offset_after_write"], fixed["logical_size"])
        stored = actual["contents"]
        zipped = base64.b64decode(stored["zlib_base64"], validate=True)
        decoder = zlib.decompressobj()
        raw = decoder.decompress(zipped, 65537)
        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail or len(raw) > 65536:
            raise AssertionError(name + ": 圧縮保存形式または上限に不一致")
        # 実験コードはインポートしない。事前の整数と末尾のバイトから独立に構成する。
        wanted = bytes(fixed["zero_prefix_bytes"]) + bytes.fromhex(fixed["last_byte_hex"])
        same(name + ": 全読取りバイト", raw, wanted)
        same(name + ": 保存長", stored["uncompressed_bytes"], len(raw))
        same(name + ": 保存hash", stored["sha256"], hashlib.sha256(raw).hexdigest())
        same(name + ": 先頭16バイト", actual["read_first_16_hex"], "00" * 16)
        same(name + ": 末尾2バイト", actual["read_tail_2_hex"], "0058")
        same(name + ": EOF", actual["read_at_eof_hex"], fixed["read_at_eof_hex"])
        full_contents.append(raw)
    same("両ファイルの全内容一致", full_contents[0] == full_contents[1], expected["contents_equal"])
    same("実験側の一致記録", observation["contents_equal"], expected["contents_equal"])
    for name in ("seek_only", "sparse_written", "dense_written"):
        stat = observation[name]["stat"]
        blocks = stat["blocks_512"]
        if blocks is not None and (type(blocks) is not int or blocks < 0):
            raise AssertionError(name + ": st_blocksが非負整数でない")
        same(name + ": OS報告値の単位換算", stat["reported_allocated_bytes"], None if blocks is None else 512 * blocks)
    same("割当量の大小を固定しない", expected["allocation_relation"], "unconstrained")
    same("一時ファイルの削除", observation["cleanup_complete"], True)
    same("対象ファイル", observation["owned_files_before_cleanup"], ["dense.bin", "sparse.bin"])
    for key in ("durability_proven", "performance_comparison"):
        same(key, observation[key], expected[key])
    same("fsyncなし", observation["fsync_called"], False)
    return checks


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("使い方: python3 -B verify.py observations/run.json")
    observation_path = Path(sys.argv[1])
    try:
        raw = observation_path.read_bytes()
        checks = check(json.loads(raw))
        print(json.dumps({"passed": True, "checks": checks, "check_count": len(checks),
                          "observation_sha256": hashlib.sha256(raw).hexdigest(),
                          "fresh_experiment_during_verification": False,
                          "visual_browser_qa": "未実施：実ブラウザツールが提供されていない"}, ensure_ascii=False, indent=2))
    except (KeyError, TypeError, ValueError, AssertionError, zlib.error) as error:
        print(json.dumps({"passed": False, "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)

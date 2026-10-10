#!/usr/bin/env python3
"""64 KiB 以下の新規一時ファイル2個だけを使い、OSの返値を記録する。"""
import base64
import hashlib
import json
import os
import platform
import sys
import tempfile
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIMIT = 65536


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stat_record(fd):
    stat = os.fstat(fd)
    blocks = getattr(stat, "st_blocks", None)
    return {
        "logical_bytes": stat.st_size,
        "blocks_512": blocks,
        "reported_allocated_bytes": None if blocks is None else blocks * 512,
        "sample_point": "書込み後・close前（fsyncなし）",
    }


def write_all(fd, data):
    returns = []
    offset = 0
    while offset < len(data):
        count = os.write(fd, data[offset:])
        if count <= 0:
            raise RuntimeError("書込みが進まなかったため停止")
        returns.append(count)
        offset += count
    return returns


def read_contents(fd):
    # pread は通常のファイル位置を動かさない。短い読取りにも対応する。
    data = bytearray()
    reads = []
    while len(data) < LIMIT:
        offset = len(data)
        chunk = os.pread(fd, LIMIT - offset, offset)
        reads.append({"offset": offset, "requested": LIMIT - offset, "returned": len(chunk)})
        if not chunk:
            break
        data.extend(chunk)
    raw = bytes(data)
    return raw, {
        "uncompressed_bytes": len(raw),
        "zlib_base64": base64.b64encode(zlib.compress(raw)).decode("ascii"),
        "sha256": digest(raw),
        "read_calls": reads,
    }


def written_record(fd, returns):
    raw, contents = read_contents(fd)
    return raw, {
        "write_returns": returns,
        "offset_after_write": os.lseek(fd, 0, os.SEEK_CUR),
        "stat": stat_record(fd),
        "contents": contents,
        "read_first_16_hex": os.pread(fd, 16, 0).hex(),
        "read_tail_2_hex": os.pread(fd, 2, LIMIT - 2).hex(),
        "read_at_eof_hex": os.pread(fd, 1, LIMIT).hex(),
    }


def collect():
    if os.name != "posix" or not hasattr(os, "pread"):
        raise RuntimeError("この実験は pread を備える Mac / Unix 環境が必要")
    start = time.monotonic()
    result = {
        "schema": "atlas.sparse-file.observation.v1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "attempt": 1,
        "retry": 0,
        "toolchain": {
            "os": platform.system(), "release": platform.release(),
            "machine": platform.machine(), "python": platform.python_version(),
        },
        "source_bindings": {name: digest((HERE / name).read_bytes())
                            for name in ("expected.json", "experiment.py")},
        "limits": {"files": 2, "max_file_bytes": LIMIT, "external_path_input": False},
        "fsync_called": False,
        "durability_proven": False,
        "performance_comparison": False,
        "filesystem_type": "未調査（OS名から推定しない）",
    }
    with tempfile.TemporaryDirectory(prefix="atlas-sparse-owned-") as temp:
        temp_path = Path(temp)
        with (temp_path / "sparse.bin").open("x+b", buffering=0) as sparse:
            fd = sparse.fileno()
            position = os.lseek(fd, LIMIT - 1, os.SEEK_SET)
            result["seek_only"] = {
                "offset": position,
                "stat": stat_record(fd),
                "read_at_zero_hex": os.pread(fd, 1, 0).hex(),
                "read_at_cursor_hex": os.pread(fd, 1, position).hex(),
            }
            result["seek_only"]["stat"]["sample_point"] = "seek後・書込み前"
            sparse_bytes, result["sparse_written"] = written_record(fd, write_all(fd, b"X"))
        # 対照：先頭から全65536バイトを書き込む。同じ内容でも割当量は制約しない。
        dense_input = bytearray(LIMIT)
        dense_input[-1] = ord("X")
        with (temp_path / "dense.bin").open("x+b", buffering=0) as dense:
            fd = dense.fileno()
            dense_bytes, result["dense_written"] = written_record(fd, write_all(fd, dense_input))
        result["contents_equal"] = sparse_bytes == dense_bytes
        result["owned_files_before_cleanup"] = sorted(p.name for p in temp_path.iterdir())
    result["cleanup_complete"] = not temp_path.exists()
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    result["elapsed_seconds"] = round(time.monotonic() - start, 6)
    return result


if __name__ == "__main__":
    if len(sys.argv) != 1:
        raise SystemExit("引数は受け付けません。新規一時ファイルだけを使います。")
    print(json.dumps(collect(), ensure_ascii=False, indent=2))

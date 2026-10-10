#!/usr/bin/env python3
"""One bounded run, three owned names and two six-byte regular files only."""
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import tempfile
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
NAMES = {"original":"original.bin", "alias":"alias.bin", "copy":"copy.bin"}

def now():
    return datetime.now(timezone.utc).isoformat()

def snapshot(directory):
    result = {}
    for label, filename in NAMES.items():
        p = directory / filename
        try:
            stat = p.stat()
            with p.open("rb") as stream:
                content = stream.read(7)
            result[label] = {"exists": True, "identity": {"dev": stat.st_dev, "ino": stat.st_ino},
                             "nlink": stat.st_nlink, "size": stat.st_size,
                             "read_hex": content.hex(), "read_bytes": len(content)}
            if len(content) > 6 or stat.st_size > 6:
                raise ValueError("owned file exceeded the six-byte bound")
        except FileNotFoundError as error:
            result[label] = {"exists": False, "errno": error.errno, "errno_name": errno.errorcode.get(error.errno)}
    return result

def collect():
    started = time.monotonic()
    result = {"schema":"atlas.hardlink-copy.observation.v1", "started_at":now(),
              "attempt":1, "retry":0, "toolchain":{"os":platform.system(),"release":platform.release(),"machine":platform.machine(),"python":platform.python_version()},
              "source_bindings":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ["expected.json","HAND_TRACE.md","experiment.py","verify.py"]},
              "limits":{"max_names":3,"distinct_regular_files":2,"max_bytes_per_file":6,"timeout_seconds":5},
              "events":[], "phases":[], "expected_failures":[], "unexpected_errors":[],
              "collection_complete":False,"timeout":False,"cleanup_complete":False,
              "filesystem_type":"not identified", "fsync_called":False,
              "claims":{"physical_block_sharing_proven":False,"all_metadata_independence_proven":False,"durability_proven":False,"performance_comparison":False,"held_fd_after_unlink_tested":False}}
    temporary = None
    old_handler = None
    def timeout(signum, frame):
        raise TimeoutError("five-second owned experiment limit")
    try:
        priority_before = os.getpriority(os.PRIO_PROCESS, 0)
        if priority_before < 10:
            os.nice(10-priority_before)
        result["priority"] = {"before":priority_before,"after":os.getpriority(os.PRIO_PROCESS,0)}
        if result["priority"]["after"] < 10:
            raise RuntimeError("low priority not applied")
        old_handler = signal.signal(signal.SIGALRM, timeout)
        signal.setitimer(signal.ITIMER_REAL,5)
        temporary = tempfile.TemporaryDirectory(prefix="atlas-owned-hardlink-")
        directory = Path(temporary.name)
        paths = {key:directory/value for key,value in NAMES.items()}
        def checkpoint(name):
            result["phases"].append({"id":name,"files":snapshot(directory)})
        with paths["original"].open("xb") as stream:
            n = stream.write(b"ALPHA\n")
        result["events"].append({"operation":"create_original","outcome":"normal","write_bytes":n})
        checkpoint("created")
        os.link(paths["original"], paths["alias"])
        result["events"].append({"operation":"create_hardlink","outcome":"normal"})
        with paths["original"].open("rb") as source:
            copied = source.read(7)
        if len(copied) != 6:
            raise ValueError("copy source not six bytes")
        with paths["copy"].open("xb") as destination:
            n = destination.write(copied)
        result["events"].append({"operation":"copy_content_to_new_file","outcome":"normal","read_hex":copied.hex(),"write_bytes":n})
        checkpoint("linked_and_copied")
        try:
            os.link(paths["original"], paths["alias"])
        except OSError as error:
            failure = {"operation":"duplicate_link","outcome":"expected_failure" if error.errno==errno.EEXIST else "unexpected_failure","exception_type":type(error).__name__,"errno":error.errno,"errno_name":errno.errorcode.get(error.errno)}
            result["events"].append(failure)
            if error.errno != errno.EEXIST:
                raise
            result["expected_failures"].append(failure)
        else:
            raise RuntimeError("duplicate destination unexpectedly accepted")
        checkpoint("duplicate_link_rejected")
        with paths["alias"].open("r+b") as stream:
            n = stream.write(b"BRAVO\n")
        result["events"].append({"operation":"overwrite_alias_in_place","outcome":"normal","write_bytes":n})
        checkpoint("alias_overwritten")
        with paths["copy"].open("r+b") as stream:
            n = stream.write(b"COPY!\n")
        result["events"].append({"operation":"overwrite_copy_in_place","outcome":"normal","write_bytes":n})
        checkpoint("copy_overwritten")
        # No descriptor is kept open across unlink; remaining names are opened afresh.
        os.unlink(paths["original"])
        result["events"].append({"operation":"unlink_original_name","outcome":"normal"})
        checkpoint("original_unlinked")
        result["owned_names_before_cleanup"] = sorted(p.name for p in directory.iterdir())
        result["collection_complete"] = True
    except Exception as error:
        result["timeout"] = isinstance(error,TimeoutError)
        result["unexpected_errors"].append({"type":type(error).__name__,"errno":getattr(error,"errno",None)})
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        if old_handler is not None:
            signal.signal(signal.SIGALRM,old_handler)
        if temporary is not None:
            owned_path = Path(temporary.name)
            temporary.cleanup()
            result["cleanup_complete"] = not owned_path.exists()
        else:
            result["cleanup_complete"] = True
        result["finished_at"] = now()
        result["elapsed_seconds"] = round(time.monotonic()-started,6)
    return result

if __name__ == "__main__":
    result = collect()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result["collection_complete"] and result["cleanup_complete"] and not result["unexpected_errors"] else 1)

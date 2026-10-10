# 一次資料locatorと実装binding

2026-10-05確認。公式索引取得と本文取得を区別する。POSIX Issue 8の直接openは403だったが、検索索引からpipe/read/dupの記述を確認した。実験はDarwinのuser-space標準APIであり、Issue 8全体への適合試験ではない。

| ID | 原典locator・節 | 実装/判断との対応 |
|---|---|---|
| PIPE | [The Open Group POSIX Issue 8 pipe()](https://pubs.opengroup.org/onlinepubs/9799919799/functions/pipe.html), DESCRIPTION / EXAMPLES | [experiment.py](experiment.py)のos.pipe、read/write endpointsと不要FDのclose。検索索引確認。 |
| READ | [POSIX read()](https://pubs.opengroup.org/onlinepubs/9799919799/functions/read.html), pipe empty / writers present / EOF | [child.py](child.py)のos.read(fd,256)。bufferが空でwriterが全closeならEOF。writerが残る空pipeはblocking。検索索引確認。 |
| DUP | [POSIX dup()](https://pubs.opengroup.org/onlinepubs/9799919799/functions/dup.html), DESCRIPTION | dupは同じopen file descriptionへの別FD参照。[異常実験](experiment.py)でduplicate write-endを残す。検索索引確認。 |
| SIGNAL | [POSIX signal.h](https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/signal.h.html), SIGTERM default action; [wait()](https://pubs.opengroup.org/onlinepubs/9699919799/functions/wait.html) status and reaping | signal.hはlocatorのみ。wait検索索引確認。SIGTERMはchildの終了であってread EOFではない。 |
| PY | [Python subprocess docs](https://docs.python.org/3/library/subprocess.html), Popen pass_fds / wait timeout / send_signal / returncode | Web本文確認。bounded waitはchildを自動終了させないため、所有childのsignal/close/waitを分ける。Python APIのnegative returncodeはPOSIX signal番号。今回実行Python 3.9.6。 |
| CLOCK | [Python 3.9 time.monotonic](https://docs.python.org/3.9/library/time.html#time.monotonic), clock reference point; [current time docs](https://docs.python.org/3/library/time.html#time.monotonic) changed in 3.10 on macOS | 版本文locator。実測[clock discovery](evidence/clock-discovery.json)によりprocess間monoを比較しない。wall_nsは表示用、NTP等で動き得る。 |
| DARWIN | [Apple Kernel Programming Guide](https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/KernelProgramming/About/About.html), Mach / BSD / VM / synchronization / I/O | Web本文・目次確認。user-spaceの観察からkernel改造・実装確認へ進むための歴史的guide。現行kext導入の指示ではない。 |
| LINUX | [Linux Kernel documentation](https://docs.kernel.org/), Core API / locking / mm / scheduler / filesystems / driver API | Web目次確認。Linux-specificな実装の次教材の公式入口。今回Linux runtimeを実行していない。 |

[ケース入力](cases.json)→[実行原票](evidence/raw.json)→[独立oracle](oracle.py)→[観測metadata](evidence/run.json)→[artifact binding](evidence/integrity.json)を辿れる。原票に保存されるのはこの実験自身のprocess/FD/event/stdoutで、host全体のprivate logや環境変数ではない。

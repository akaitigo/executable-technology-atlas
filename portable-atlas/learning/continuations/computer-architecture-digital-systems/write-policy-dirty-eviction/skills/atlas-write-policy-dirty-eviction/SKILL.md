---
name: atlas-write-policy-dirty-eviction
description: WTとWBのdirty evictionおよび有限flush模型を既存runnerと実UIで比較する。
---

# 案内

write-through、write-back、dirty、eviction、flush、write-allocateの問いは[README](../../README.md)、[UI](../../index.html)、[route](../../route.py)に案内し単元で`python3 verify.py`を実行する。旧rawを上書きしない。cacheとbacking memory、victim address、transactionとbyte数を区別する。

[原典](../../sources.json)と[coverage](../../coverage.json)へ接続する。実CPU・cycle・coherence・ordering・電源断・永続性は未対応。flushをfsyncと説明しない。新依存/課金/global Skill/旧単元変更を行わない。

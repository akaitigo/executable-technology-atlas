---
name: atlas-storage-locking
description: Navigate the existing Mac two-process lost-update and stable-lockfile continuation; use for its saved timeline and checks, not provisioning or durability claims.
---

From the continuation root, route `locking` to [experiment.py](../../experiment.py), `verify` to [checker.py](../../checker.py), `timeline` to [index.html](../../index.html), `sources` to [SOURCES.md](../../SOURCES.md), using [route.py](../../route.py).
Default commands read saved evidence. Only explicit `--record` reruns owned temp/process experiments; `--record-binding` seals bindings. Preserve raw failures; do not refresh observations merely to pass a checker.
Explain atomic visibility, complete read-modify-write isolation, and durability separately. Saved observations are Mac-specific controlled schedules. Native NFS/Linux, power loss, targetinode-lock correctness, speedup and arbitrary input/path/command execution are unsupported; route them to [README limits](../../README.md). Do not extend resources or claim the whole Subject complete.

---
name: atlas-mmap-visibility
description: Navigate the existing actual-Darwin shared/private/readonly mmap visibility lesson and saved API refusals; excludes kernel internals and durability claims.
---

From this continuation root use [route.py](../../route.py): `visibility` → [record.py](../../record.py), `verify` → [checker.py](../../checker.py), `timeline` → [index.html](../../index.html), `sources` → [SOURCES.md](../../SOURCES.md).
Normal commands read evidence. Explicit `--record` creates unique new raw or failed partial raw, preserving older observations. `--record-binding` updates only artifact bindings; do not rewrite expectations or raw to hide failures.
Read [EXPECTATIONS](../../EXPECTATIONS.md) and [literal oracle](../../oracle.json): private-copy mapping bytes may change while file bytes do not. Shared runtime visibility and successful flush are different from power-loss durability. Mapping close and file close are separate resources.
Only bounded Python API refusals are demonstrated. Route pagefault counts, physical COW pages, crossprocess, Linux/Windows, kernel modification and power-loss claims as unsupported using [README limits](../../README.md). Do not introduce pointer/truncate/unsafe-signal experiments or hardware/service setup.

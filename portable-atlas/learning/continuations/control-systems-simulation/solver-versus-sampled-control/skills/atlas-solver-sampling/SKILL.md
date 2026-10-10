---
name: atlas-solver-sampling
description: Navigate the fixed-T mathematical solver versus sampled-hold control continuation, including saved traces and checks; excludes hardware control and PID-wide claims.
---

From this continuation root, use [route.py](../../route.py): `sampling` → [record.py](../../record.py), `verify` → [checker.py](../../checker.py), `timeline` → [index.html](../../index.html), `sources` → [SOURCES.md](../../SOURCES.md).
Default reads saved evidence. Only explicit `--record` creates a new UTC/UUID run, preserving previous raw files; `--record-binding` seals artifact hashes. A check failure does not authorize changing expectations or rewriting observations.
Explain forward/backward Euler as solvers for the continuously closed loop, and plant-exact/sample-held control as a different controller model. Read the [derivation](../../DERIVATION.md) before interpreting stability or terminal differences. Fixed T and axis scales matter. Critical boundary series were not executed.
Route HIL, real plant, PID entirety, safety guarantees, arbitrary gain/clip/delay, installation and real controller tuning as unsupported, using [README limits](../../README.md). Do not start services or resources beyond this continuation's authorized preview.

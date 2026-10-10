---
name: atlas-footprint-clearance
description: Navigate the existing fixed-route circular-footprint and C-space geometry continuation; excludes ROS execution, planning and robot safety claims.
---

From this continuation root use [route.py](../../route.py): `footprint` → [record.py](../../record.py), `verify` → [checker.py](../../checker.py), `diagram` → [index.html](../../index.html), `sources` → [SOURCES.md](../../SOURCES.md).
Default commands read saved evidence. Explicit `--record` creates a fresh raw run and preserves old files; `--record-binding` seals artifact bindings. Do not change expectations or observations to hide check failures.
Read [EXPECTATIONS](../../EXPECTATIONS.md): closed contact is collision; rounded circular inflation is not an expanded box. The independent original-obstacle distance oracle and inflated-region producer use different constructions. Discrete pose sampling is intentionally bad for the middle-obstacle example.
Circle displays are inspection probes, not physical movement. Route ROS, real robot, polygon pose, sensor uncertainty, braking, safety and arbitrary route planning as unsupported, referring to [README limits](../../README.md). Keep this local skill scoped to the finite mathematical continuation.

---
name: atlas-async-completion
description: Inspect this finite Node Promise completion lesson with explicit gates, fixed schedules and actual TAP evidence; route OS races or all flaky causes as unsupported.
---

Start with [README](../../README.md) and [expectations](../../EXPECTATIONS.md). Supported route.py topics are completion/verify/compare/sources. Normal runner/checker reads saved evidence without running Node or changing files.

For explicitly requested new evidence run runner.py --record in this module. Source is copied to an owned private temp so raw TAP does not expose workspace paths. Preserve original failures and old unique raw. Runner owns only its test processes/streams/temp source copies. Expected assertion failure is not unexpected execution failure; unsupported input has test-file exit2 and outer Node runner exit1.

Use [literal event/value oracle](../../oracle.json) and [independent validator](../../oracle.py), neither imports producer. Both variants use the same assert body; schedules control test start and gate release. before/awaited starts the test first but its assert waits until update. Use work completion Promise, not test registration Promise, as the dependency. Do not add sleep to make a case pass.

Explicit checker.py --record-binding updates only module digests. No global install or changes to existing servers/units. OS races, all flaky causes, mock timer behavior, CI and performance remain unsupported; use README next experiments.

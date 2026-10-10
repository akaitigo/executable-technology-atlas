---
name: atlas-wsgi-boundaries
description: Inspect this finite stdlib WSGI request ownership lesson with actual HTTP and saved SQLite evidence; route framework, TLS and concurrency as unsupported.
---

Start with [README](../../README.md) and [contract](../../EXPECTATIONS.md). Supported route.py topics are http/verify/compare/sources. Normal runner/checker reads current evidence; checker runs only read-only SQL, never sends new HTTP.

For an explicitly requested new observation, run runner.py --record in this module. Preserve old and failed run directories. Runner owns only its loopback dynamic servers/threads/clients/live temp DBs. Saved SQLite snapshots are evidence, not temporary cleanup targets. Existing servers and units are outside scope.

Use [literal table](../../oracle.json) and [independent SQL oracle](../../oracle.py); it imports no adapter/runner. Normal 201, transport/input refusal and expected SQL 500 have separate outcomes. Compare fault location, rollback, DB snapshot, connection close probe, response start and recovery's new connection. WSGI input/errors are server-owned and must not be closed by app. Do not count the preexisting same-transaction outbox concept as new coverage.

Explicit checker.py --record-binding updates this module digest only. Framework DI/auth/TLS/concurrency/chunked/sending-after-failure claims are unsupported; consult README next experiments. This local Skill is not globally installed.

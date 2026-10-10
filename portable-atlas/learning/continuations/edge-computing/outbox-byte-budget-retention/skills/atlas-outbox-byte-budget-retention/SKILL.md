---
name: atlas-outbox-byte-budget-retention
description: Inspect the finite UTF8 byte-budget outbox lesson using owned SQLite persistence, separate read-only reopen, literal hex expectations, bounded mutable payloads, and intentional character-count overflow.
---

Use only this module. Read ../../README.md, ../../fixtures.json, ../../hand-oracle.json and ../../observations/verification.json. Run python3 -B check.py and python3 -B route.py outbox-byte-budget-retention from the module root as read-only checks. Unsupported topics exit 2. Do not run --record unless new observations are explicitly requested. Preserve old raw, other modules and Core/fullGate. Explain payload bytes versus DB disk size, seed initialization versus new-operation write count, capacity rejection versus input rejection and execution failure. Do not claim Greengrass compatibility, TTL immediate deletion, crash durability or real edge networking. Close only module-owned preview resources.

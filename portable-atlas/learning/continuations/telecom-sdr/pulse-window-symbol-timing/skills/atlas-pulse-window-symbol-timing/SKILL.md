---
name: atlas-pulse-window-symbol-timing
description: Inspect the finite BPSK pulse and sample-window timing lesson, distinguishing declared zero padding, insufficient windows, erasures, and the intentional zero-to-bit0 fault.
---

Use only this module. Read ../../README.md, ../../fixtures.json, ../../hand-oracle.json and ../../observations/verification.json. Run python3 -B check.py and python3 -B route.py pulse-window-symbol-timing from the module root as read-only checks. Unsupported subjects must exit 2. Do not run --record unless new observations are explicitly requested. Keep existing raw, other modules, Core and fullGate unchanged. Explain known offsets 0/1 and the finite boundary policy; do not claim RF, timing recovery, matched-filter optimality or statistical BER. For UI checks use the module-owned dynamic localhost server and browser tab, then close only those resources.

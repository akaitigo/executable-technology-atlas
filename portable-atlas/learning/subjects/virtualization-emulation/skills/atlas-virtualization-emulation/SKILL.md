---
name: atlas-virtualization-emulation
description: この有限Tiny8 LOAD/ADD/JZ/HALT教材のwrap・PC/fetch・width省略異常・budget拒否を既存runner/checker/register-memory UIへrouteする。実VM boot、hypervisor、isolationや実ISA互換の検証には使わない。
---

rootは`../..`。[README](../../README.md)・[SPEC](../../SPEC.md)で作者定義ISAとinput、[coverage](../../COVERAGE.md)で次の4実験、[sources](../../SOURCES.md)で原典bindingを確認。

- `python3 -B route.py emulator|verify|register-memory|sources`は既存runner.py/checker.py/index.html/SOURCES.mdへrouteする。別emulatorや依存を増やさない。
- `python3 -B runner.py`またはREADMEの`--input-json`はread-only。HALT exit0、input/execution拒否exit2。input拒否のtraceなしとbudget拒否の有限traceありを区別。
- `python3 -B checker.py`は通常read-only。原票再観測の明示依頼にだけ`python3 -B observe.py --write-evidence`。binding更新の明示依頼にだけ`python3 -B checker.py --seal-evidence`。hash更新を新しい実行証拠と呼ばない。
- [UI](../../index.html)は予想→step replay→正常/異常register・memory・独立table/handtrace比較→原典/実装→答え。文書viewerとdynamic loopback previewを使い、専用serverを終了する。
- [raw](../../evidence/raw.json)/[run](../../evidence/run.json)の時刻・環境・digestを示す。naive-unboundedはinteger/PC幅の反例で、両variantともstep budgetを守る。実VM/CPU互換やhost isolationの証拠へ転用しない。

vm-boot、hypervisor、isolation、jit、devices、migration、real-isaや任意未定義topicはunsupported/exit2で[coverage](../../COVERAGE.md)の具体的問い/公式locatorへ案内。新依存、権限追加、host設定、課金、公開へ拡張しない。

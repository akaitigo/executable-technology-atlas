---
name: atlas-store-code-cache-invalidation
description: 独自Tiny8 STOREのcode書換えとdecoded block失効を固定10ケースで比較する。QEMU実行・native JIT・実ISA・VM boot/isolation・速度改善には使わない。
---
README→元Tiny8→今回SPEC→contracts→producer前固定expected-tableを読み、route.pyの有限入口に対応づける。
予想→Python原票のPC/A/memory差分→fetch/invalidate/stale→address範囲とQEMU原理→答えを辿る。
STOREは0x40 addr8、memory[addr]=A、A保持。blockのopcodeとoperand両byteを依存範囲へ含める。wrap255のoperand0を忘れず、code外・unrelated blockを保持する。STOREでblockを終え次PCへlookupする。
input拒否、illegal opcode、step budget、HALTを区別する。全予想control単独変更は新値保持、旧比較・trace・答え本文を空にしdetailsを閉じる。UIは保存reader。
通常checker/runnerはread-only、hash/mtime不変。明示runner --recordだけfresh原票を作り旧rawを保持する。native/QEMU/実ISA/isolation/性能保証は除外しcoverageへ案内する。公開・install・設定・課金は行わない。

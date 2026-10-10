---
name: atlas-graphics-rendering
description: この教材のPython CPU rendererと拡大PNGでtriangleのedge coverage・barycentric depth・描画順の違いを学ぶ。実GPU、完全clip規則、物理照明の実装保証には使わない。
---

# CPU triangle教材

教材rootはこのSkillの二階層上。[README](../../README.md) の起動と操作、[検証記録](../../VERIFICATION.md) の実測、[未教材領域](../../scope.json) へ案内する。新しいrendererを別に作らず `raster.py`・`verify.py`・既存UIを使う。

- 通常checkerは `python3 -B verify.py`、保存原票照合は `python3 -B verify.py --check observations/cpu-attempt-01/run.json`、Browser/Artifact照合は `node audit.mjs`。全てread-only。新規原票は求められた場合だけ `--record 未使用名` で作り、既存原票を上書きしない。
- `node serve.mjs` のtask-owned loopback URLで、予想→normal-ab/ba切替→sample(7,5)→Source→回答を試す。共有辺はshared-ab/baの(5,5)を調べる。
- sampleはpixel中心、y下向き、top-left共有辺、strict LESS、同depth先勝ち。正常の順序不変を同depthにも一般化しない。BrowserはCPU PNGをdecodeして表示するので、GPU rasterizerの実証ではない。
- GPU shader/driver、完全clipping、lighting等の依頼には `scope.json` の未制作範囲を説明し、この教材だけで保証しない。課金・依存導入・権限/設定変更・公開をSkill利用から推定しない。

raw原票を読む際、Python実演算・独立oracle・Browser decode観測を区別する。同一Agentのrouting確認を独立Forward Evalと呼ばない。

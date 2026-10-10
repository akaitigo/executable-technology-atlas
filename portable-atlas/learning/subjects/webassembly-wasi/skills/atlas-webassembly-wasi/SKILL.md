---
name: atlas-webassembly-wasi
description: 既存の41byte core moduleと実Browser/Nodeのrunner・UI・checkerでi32.add、wrapping、JS値変換とmodule/import拒否を学ぶ。WASI/Component実行や全runtime保証には使わない。
---

# 小さなcore moduleの境界へ案内する

このSkillからmodule rootは`../../`。READMEとscope.jsonを読む。「Wasm足し算がJSと違う」「binary/type/importの失敗を区別したい」は対応route。予想→固定入力UI→rawと表・説明stackの比較→binary.mjs/experiment.mjs/oracle.mjsと原典→答えへ案内する。

`node verify.mjs`は実NodeのWebAssembly、`node check.mjs`は保存実BrowserとNode原票のread-only照合。`node serve.mjs`のloopback URLで実Browserを操作する。原票更新は明示`--record observations/未使用名`のみ、Browser raw/画像も新規保存。Source変更時に実再取得し、成功/拒否の旧原票を保持。自分のtab/serverだけ終了する。

i32.addはmodulo 2³²、JS返値はsigned。JS Numberを無限精度整数と呼ばない。小数はJS APIで先にi32変換。BigIntをi32へ渡すTypeErrorと不正moduleのCompileError、import不備のLinkErrorを区別する。stack図は算術モデルの説明でengine内部Traceとは呼ばない。

正常routeはUIの2+3を選択してEnter、結果5/raw/oracleを比較。未対応route「WASIでファイルを読み、Component化し全runtime保証」はREADME E2/E3/E4へ案内し未制作を伝える。依存install、権限変更、global設定、公開を勝手に行わない。同一Agentのroute確認は独立Forward Evalではない。

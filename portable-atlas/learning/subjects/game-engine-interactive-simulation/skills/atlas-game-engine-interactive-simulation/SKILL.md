---
name: atlas-game-engine-interactive-simulation
description: 固定刻みaccumulatorとvariable Eulerの運動・薄床・pause・delta capを、この有限Browser教材で比較する。実ゲームengineやネットワーク同期の検証には使わない。
---

教材rootのREADME.mdを読み、既存cases.json、model.mjs、oracle.mjs、UIを使う。frameは2入力のfixtureで、実FPSではない。

- 予測→入力選択→「選択入力を実行」→比較→「答えと判断条件を見る」へ案内する。薄床の反例はfloor-balanced、高速の限界はfast-tunnel、時間破棄はpaused/tab-cap。keyboardではrunボタンにfocusしてEnterで実行できる。
- 読み取り検証はrootで `node verify.mjs` と `node check.mjs`。新しい実行原本を保存する場合だけ `--record observations/NEW-ID` を指定する。既存directoryを上書きしない。Browserは既存serve.mjsで動的localhostを作り、通常のUI操作で実行し、使ったtab/serverだけ閉じる。
- fixedが決定性やCCD、engine精度を保証すると説明しない。step traceはtoy recurrenceの記録、timestampは実行時刻、diagramはraw stateの表示である。
- 実engine/CCDはE1、scene/assetはE2、input/audio/render/performanceはE3、network/replayはE4へscope.jsonの未制作経路を案内する。依存の追加、engine install、Cloud利用や権限変更へ勝手に進まず、未実行を明示する。
- Skillの同一agent routing試験は独立Forward Evalではない。Subject/全体Goalの完成をこの教材のpassから推定しない。

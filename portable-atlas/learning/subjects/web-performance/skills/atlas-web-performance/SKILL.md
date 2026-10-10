---
name: atlas-web-performance
description: この小grid教材でDOM read/write順序の実時間・geometry一致・timerと同期占有を既存runner/checker/UIで学ぶ。LCP/INP全証明や本番性能保証には使わない。
---

# 既存Layout / Timer教材へ案内する

module rootはこのSkillから`../../`。READMEとscope.jsonを読む。「交互とbatchedの違いを測りたい」「timerとblockingを区別したい」は既存serve.mjsとUIへroute。予想→固定workload操作→raw/geometry/elapsed比較→experiment.mjs/oracle/原典→答えへ案内する。

16セル・8反復・warmup2・本測定5の条件を保持。順を交互にし、0msや外れ値を消さず、batchedの勝ちを必須にしない。geometry一致と測定の主張を分ける。probeは20/100ms timerと120ms同期占有であり、実ユーザー入力やINPではない。約120ms同期停止を事前に伝える。

純計画はnode verify.mjs、保存実Browserはnode check.mjsでread-only確認。原票更新は明示--record未使用directory、Browser再取得は実操作と画像を新規保存。Source変更をhash追記だけで実証扱いしない。own tab/serverのみ終了。

「本番のLCP/INPを全面保証」「RUMを収集」「全Web performanceを完成」「workerへ自動移行」は未対応route。README/indexのE1–E4の実験案/公式locatorへ案内し、現教材で保証しない。新依存/外部収集/公開/global installの許可は含まない。同一Agentのroute確認は独立Forward Evalではない。

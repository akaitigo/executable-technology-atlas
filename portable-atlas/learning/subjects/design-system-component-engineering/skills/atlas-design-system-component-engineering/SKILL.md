---
name: atlas-design-system-component-engineering
description: この教材のCSS token継承・button instance上書き漏れ・不正色fallback・native disabledとkeyboard比較を既存UIとcheckerで学ぶ。実package配布やdesign system全体の実装保証には使わない。
---

# 既存Token / Button教材へ案内する

module rootはこのSkillから`../../`。READMEの学ぶ順番とscope.jsonを読む。通常routeは「A色が隣へ漏れる理由を学びたい」「不正色はfallbackになるか」「disabledとkeyboardを比較したい」。既存serve.mjsを起動し、予想→既存UI操作→computed style/DOM属性と左右比較→styles.css/api.mjs/一次資料→答えへ案内する。

6桁hexの局所APIとnative primary buttonのみ。not-a-colorは左へ生値、右は検証してinstance値を削除。未定義fallbackと計算時不正を混同しない。既存原票はnode check.mjs、pure APIはnode verify.mjsでread-only照合。新原票は明示--record未使用directory、Browser取得は実操作と画像を新規保存する。source変更をhash更新だけで実証済み扱いしない。専用tab/serverを終了し、他taskへ触れない。

「token pipeline全実装」「実package配布」「Shadow DOM保証」「全WCAG適合」「全design system完成」は未対応route。README/indexの4実験案と公式locatorへ案内し、既存の一教材で保証しない。新依存/global Skill install/公開/GitHub操作の許可は含まない。同一Agentのroute確認と独立Forward Evalを区別する。

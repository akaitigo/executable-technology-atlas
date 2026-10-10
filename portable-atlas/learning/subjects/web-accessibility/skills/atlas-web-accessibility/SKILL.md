---
name: atlas-web-accessibility
description: この教材でnative buttonとclick-only divのTab・Enter・Space・focus・accessible role/nameを比較し、名前欠落例と修正版を試す。WCAG全体の適合判定や未制作widgetの実装には使わない。
---

# ボタン操作と名前の教材

このSkillから二階層上が教材root。起動は `node serve.mjs`、通常の検査は `node verify.mjs`。操作の順序・一次資料は [README](../../README.md)、実測と未測定は [VERIFICATION](../../VERIFICATION.md)、未制作領域は [scope.json](../../scope.json) にある。

保存観測は `node verify.mjs --browser observations/browser-attempt-01/browser.json` と `node audit.mjs` で結果・fresh trustedイベント・負例を照合する。

- UIで予想 → Tab/Enter/Space/クリック → 実装比較 → 名前欠落/修正 → 回答へ案内する。
- role+tabindexだけの例は到達可能でもキー動作しない。修正版を実イベントで確認する。DOM文字やrole属性からcomputed nameを推測せず、ブラウザのrole/name観察と分ける。
- 通常checkerはread-only。新しい記録を求められたときだけ `--record 未使用名`。既存観測は上書きしない。`--browser observations/観測名/browser.json` は保存記録の照合で、新規Browser実証ではない。
- この教材外のWCAG認証、全支援技術動作、dialog/フォーム等の依頼には未対応範囲を説明する。教材の成功をSubject全体の保証へ広げない。

実操作は利用者の許可範囲で行う。新規依存・OS設定・グローバルSkill導入・公開をこのSkillの使用だけで開始しない。

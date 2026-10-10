---
name: atlas-modal-focus-lifecycle
description: 既存の2-control fixtureでnative dialogとrole-only divのinitialfocus、Tab/ShiftTab、Escape、復帰を実Browserで比較する。実AT/WCAG全適合/OS設定変更は対象外。
---

このrootのREADME.md、plan.json、oracle.mjsを読み、既存serve.mjs/UI/check.mjsを使う。元ボタン教材とXRはread-only。

- 予想→native-basic選択→準備（起点focusのみprogrammatic）→Enter/Tab/Shift+Tab/Escapeの実Browser入力→activeElement/DOM/AX比較→原典/答えへ案内する。native-wrapのBODY等もinsideに書き換えずAPG期待との差として保存する。
- role-faultは意図的故障。Escape後はplanのcleanupキーで閉じ、UIを可用性の正しい実装として流用しない。独自trapを勝手に追加しない。
- 通常 `node verify.mjs` / `node check.mjs` はread-only。明示 `--record observations/NEW-ID` だけ新原票を保存する。所有tab/serverだけ終了する。
- 実AT音声・WCAG適合要求は未検証と説明し、scope.jsonのE2/E4へ案内する。OSアクセシビリティ設定、screen reader起動、device権限、依存追加へ今回の許可を拡張しない。
- Nodeのsynthetic期待列検査はBrowser操作の代替ではない。同一agent routingは独立Forward Evalではなく、入口分野数・Subject/Goal完成を増やさない。

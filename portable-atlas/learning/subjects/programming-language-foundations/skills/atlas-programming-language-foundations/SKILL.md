---
name: atlas-programming-language-foundations
description: 有限AST/closure教材でlexical scopeとcaller-parent意図異常を束縛・評価traceから比較する。既存CLI/UIと原票へrouteし、一般型体系や実言語concurrencyの検証には使わない。
---

# Closure教材へroute

教材rootはこのdirectoryの`../..`。[README](../../README.md)で道筋/入口、[Coverage](../../COVERAGE.md)で6 AST kind・literal/name/node/budget境界を確認。

- 保存観測は[run](../../evidence/run.json)の時刻/環境と[raw](../../evidence/stdout.json)。中心caseはx10→f capture→inner x20→callで正常10/異常20。normal e4→e1、異常e4→e3。未再実行を現在の実測にせず、実言語の仕様へ一般化しない。
- 通常CLIは教材rootで`python3 -B check.py --case capture`、保存検査は`python3 -B verify.py`。custom JSON ASTはREADMEの`--ast-json`例へroute。checker/optionなしobserveはstdoutだけでread-only。normal error/拒否のcustom/caseはexit2。
- 原票更新の明示依頼があるときだけ`python3 -B observe.py --write-evidence`、verify、UI reload。検査に合わせてEvidenceを自動で書き換えない。
- [UI](../../index.html)の予想→Capture→Call parent→束縛Lookup→比較→原典/実装→答えへ進む。[interpreter](../../interpreter.py)と[独立tuple oracle](../../verify.py)が実装。[環境図](../../evidence/environment-chain.svg)は実trace再描画でcaptureではない。

parameter shadowと自由変数、callerのarg評価とbody lookupを分ける。errorの値なしと正常0、AST拒否とRuntime errorとbudget停止を区別。lexical/static scopeはstatic typingではない。dynamic言語設計全体を不正扱いせず、宣言lexical semanticsへの欠陥として説明。

型推論/健全性、mutation、一般lambda計算の証明、実言語concurrency等は未教材と具体化し、READMEの未実施実験候補を案内する。新依存・OS設定・外部サービス・新権限・global Skill install・公開へ勝手に拡張しない。

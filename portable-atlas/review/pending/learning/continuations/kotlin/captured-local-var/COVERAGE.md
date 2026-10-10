# Kotlin：captured local varの対応範囲

元の分野ゴールは`2026-10-06/task-8/atlas-97-field-goals-ja.md`の「23. Kotlin」（今回読取時293–302行）です。nullable型とsmart cast、拒否/正常分岐の検証と実務判断に対応します。前教材[smart-cast-boundariesのCOVERAGE](../kotlin-smart-cast-boundaries/COVERAGE.md)に残るcaptured local varを、この1単元で小さく扱います。元の目標文書・旧教材・統合repoは変更していません。

| 観点 | 今回の固定設計 | 現在の根拠と限界 |
|---|---|---|
| 変更のないlocal var | non-capturedのAda/null 2条件 | exit 0・固定stdout一致。nullは利用を省略 |
| 書換closureによるcapture | guard後にmutateを呼び、local.lengthを使う拒否例 | exit 1・SMARTCAST_IMPOSSIBLE・JARなしを実測 |
| 変更前に受け取るlocal val | snapshotを取得→mutate→保存値の利用 | Ada/null 2条件の固定stdoutと一致。最新値の保証ではない |
| 段階別の分類 | compile受理1/拒否1、runtime正常4/異常0 | 全件を実測・独立46項目pass。拒否にruntime結果を作らない |
| 予想・操作・比較・原典・答え | 保存原票reader、README、模式図、再現runner、独立verifier | この単元でGUI 21検査・78実ポインター操作pass。1280/390pxの実capture 7枚を目視。模式図と実測を区別 |
| 変更・reset・取得失敗 | 表示rawと固定原票照合、HTTP 503/digest不一致、古い遅延success/error | 旧結果・原票・答えを消去し、新条件を上書きしないことをGUIで確認。native再実行0 |
| 既存Labとの区別 | Int加算capturedClosure、sealed型smart castを読取 | 既存例を今回の受入数へ再加算しない。検索の未発見は不存在の証明ではない |
| 残るcapture条件 | 読取専用capture・inline/contract・escape等 | 今回未検証。全ラムダへ一般化しない |
| 独立受入・統合 | 作者QAと別reviewerの判断を分離 | 最新の受入はstatus.jsonを参照。Atlas未統合・共有台帳未変更 |

観測の入口は[status.json](observations/status.json)、固定期待値は[expected.json](expected.json)、原典・既存Labとの対応は[sources.json](sources.json)です。

実測根拠は[run.json](observations/20261006T062456931814Z/run.json)、[独立検証46項目](observations/20261006T062456931814Z/verification.stdout.json)、[資源・件数要約](observations/20261006T062456931814Z/summary.json)です。[実行前の固定SHA](observations/preparation.json)と期待値・ソースの一致を保持しました。前教材のGUI/独立受入結果をこの単元へ流用していません。

GUI根拠は[検査原票](browser-qa/run-2026-10-06T064513392Z/report.json)、[実captureの目視記録](browser-qa/visual-review.json)、[修正前snapshotと最終binding](browser-qa/gui-revision-20261006T063554049947Z/final-binding.json)です。GUI補完の前後で固定source・期待値・native原票は不変です。入口は[index.html](index.html)です。

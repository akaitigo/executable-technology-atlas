# 有限の採用範囲

strict 6ケース（評価完了3、評価前の静的拒否3）、故障比較2（未初期化IDへの評価拒否1、flat scopeの値漏れ1）。全8のAST・宣言ID・値・失敗位置を手書きoracleと独立environment lookupで照合。5種の改変を拒否。実IAB全8と条件変更resetを確認。期待拒否とsandbox bind実行失敗を分ける。

producer/importと独立checkerは別実装。実evaluatorはresolverのID tableを使用し、initialize/use traceを記録。手書きoracleはraw採取前に作成。原典は著者Resolving and Binding、独自逐次宣言契約。JavaScript TDZ、closure、type checker、source parser、任意evalは未実装。Subject全体・Atlas全体完了にはしない。次の3提案はREADME、未実施。

証拠はobservationsのUTC raw、qa.json、verification.json。captureは実画面をツール表示、ローカル画像未保存。通常check/routeはhash/mtime不変で確認。全Gate、依存変更、commit/push/publicationは未実施。

---
name: atlas-static-name-resolution
description: 明示block/let/use ASTの先行宣言・最内scope・宣言ID評価を検証し、先登録/flat scope故障と比較する。JavaScript TDZ、closure、型検査、任意ソース評価には使わない。
---

教材rootは ../..。READMEの独自逐次宣言契約を先に読む。strict評価完了・期待静的拒否・故障版評価拒否を分ける。

保存原票はrootで `python3 -B skills/atlas-static-name-resolution/route.py name-resolution`。手書き宣言ID/値oracleと独立environment lookupを照合する。通常checker/routeはread-only。fresh原票を作る場合だけ明示 `runner.py --record`。

実行は `runner.py --case before-inner-let` または `server.py` の固定AST。resolverの宣言IDをevaluatorが実際に使うtraceを見る。先登録版は未来のIDが未初期化として拒否され、flat版は内側20が外へ漏れる。

javascript-tdz / closure / type-checking / arbitrary-sourceは未対応としてREADMEの範囲・次案へ戻る。言語全体の保証と呼ばない。

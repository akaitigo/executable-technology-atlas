# 検証記録

問い：引用先の存在と、今回contextが回答を支持することを分けられるか。経路：Mac直接Python標準ライブラリ→架空の固定corpus→lexical retrieval→全文章context→著者回答fixture→citation binding→HTTP→実IAB。

生成モデルは未実行。literal支持は原文1文と固定claimの一致で、semantic entailmentや世界の真実ではない。instruction-fixtureの内容は全モードでデータとして扱い、命令を実行しない。manual kindは自動検出器ではない。

独立retrieval/context/fact oracle、12case×2policy、全8参照fact、120個seed固定変形、不正入力・corpus・policy拒否を検査。通常checkerはread-only、原票更新は明示 --record。作者routing smokeは独立AgentEvalではない。

時刻・環境・input/corpus/source/artifact digestはobservations/receipt.json。実IAB、capture保存可否、ownedserver/tab終了はobservations/ui-qa.jsonへ記録する。Subject全体/生成モデル/実製品RAG/検出保証は未完成。指定外path、Portal/Core、Goal、commit/pushは変更せず、全体gate/full verifyは今回未実行。

## 実観測 — 2026-10-05 JST

Python3.9.6 / Darwin arm64。12case×2policyを実実行。正常archive/gardenは受入、誤値/誤claim/欠落context/命令fixtureはstrict拒否・citation-only受入、未知IDは双方拒否、空claimsは棄権。2claim例は支持1/2でstrict全体拒否。全8参照factと120個の固定seedquery/budget変形、不正入力10・corpus4・policy1拒否を独立oracleと照合した。source spanも原文sliceへ一致した。

Skill quick_validateと正常citation/未対応llm-generationの作者routing smoke通過。UIのNode vm.Script構文検査はブラウザ実行と区別する。

## 一時HTTP・実IAB・capture・cleanup



実IABでcase/policyを24通り操作して終端traceを読み、期待statusと照合。ui-matrix.jsonは実locator出力の転記。次buttonは全24終端でdisabled。retrieval順位のscore8/3/1/1と同点ID順、contextの除外理由、正常span[28,56]、存在IDで誤23:00の支持false、正quote17でもclaim23なら一致false、命令quoteは存在しても参照kind=false、budget0空context、著者fixtureによる棄権を確認。生成モデルの自発的棄権や一般的防御の証拠ではない。

runtime時刻・環境、入力/corpus拒否一覧、原典binding、主要9領域の問い、次の4実験を確認。実captureを5回ツール出力で目視。画像ファイルはrepoへ未保存で、local pathと画像artifact digestはない。再描画は行っていない。desktopで日本語/表/traceの重なりを認めず、mobileは未確認。

自作IAB tab4をclose、一時serverをCtrl-Cで終了しexit0を確認。HTTP logはpreview-http.logに保持。favicon404も保存し、教材JSON/receiptは200。

## 中間失敗と結合更新

初回QA結果を保存した後の通常checkerは、旧receiptのui-qa.json artifact digestと一致せず失敗した。runtime oracleの失敗ではない。失敗をQA履歴に保持し、完了QA/matrix/logを明示 --recordで結合してから通常checkerを再実行し通過した。sourceや判定gateを緩めて通していない。UIが実際に観測したraw digestも記録し、checkerが現rawとの一致を検査する。

完了QAを結合した後、plain `python3 verify.py` の前後でmodule全ファイルSHA-256一覧が不変であることを確認した。bytecode生成もなく、通常checkerはread-onlyを維持した。

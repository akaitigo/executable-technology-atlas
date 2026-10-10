# chunk境界・overlap・根拠予算

[元Subject README](../../../subjects/generative-ai-rag/README.md)のcoverage「chunk-budget」に対応する有限継続。先に元教材でcitation存在/context/原文支持を分ける。[関連IR precision-recall教材](../../information-retrieval-search/precision-recall-contract/README.md)でquery hitの評価単位と基準を確認してから、ここでchunk単位とcontext内根拠を追う。IRのprecision/recallと、このliteral支持は別scopeで、同一の評価指標ではない。

前提はPython文字slice・半開区間[begin,end)・順位・集合・予算。読む順番は原文→固定根拠span→chunk境界→overlap→retrieval hit→予算選択→context支持→実務判断。画面で3予想を置き、条件変更→実Python処理→正常/不支持/故障判断/拒否比較→原典/コード/raw→答えへ進む。

## 独自literal契約と事前表

架空3文書、ASCII本文。garden59文字の[16,36) `Gate opens at 08:00.` が固定根拠。archive24/museum22文字はquery Gateのhitなし。現実の施設情報ではない。evidence.jsonとhand-oracle.jsonの元文長/offset/ranges/予算表はproducer実行前に固定した。

24文字chunk、step=24-overlap。原文末尾へ到達したchunkで停止する。末尾でさらに完全内包chunkを作らない。retrievalはquery literalの完全一致出現数、score>0だけ、同点はdoc ID/startの順。単語・token・embedding検索ではない。rank順に各chunk全体が残りbudgetへ収まればincludeし、収まらなければ除外して次へ。予算はchunk本文のPython文字数合計で、重複も含む。header/区切り費用は含めない。

支持は「単一included chunkに、固定doc/offsetの完全literalが入る」こと。fragment同士を結合して支持へ昇格しない。索引内完全span保持、retrieved完全span、実included context支持を分ける。

| case | overlap / budget | hit offsets | 全chunkの完全span offsets | included offsets | 合計/unique/重複文字 | context支持 |
|---|---|---|---|---|---|---|
| boundary-broken | 0 / 72 | 0 | なし | 0 | 24/24/0 | false |
| overlap-retained | 12 / 48 | 0,12 | 12 | 0,12 | 48/36/12 | true |
| overlap-budget-excluded | 12 / 24 | 0,12 | 12 | 0 | 24/24/0 | false |
| heavy-overlap-excluded | 20 / 72 | 0,4,8,12,16 | 12,16 | 0,4,8 | 72/32/40 | false |
| heavy-overlap-supported | 20 / 120 | 0,4,8,12,16 | 12,16 | 0,4,8,12,16 | 120/40/80 | true |
| no-hit（Midnight） | 12 / 48 | なし | 12 | なし | 0/0/0 | false |
| bad-retrieval-hit-only | 12 / 24 | 0,12 | 12 | 0 | 24/24/0 | falseだが故障判断が受入 |
| invalid-overlap | 24 / 48 | 未実行 | 未実行 | 未実行 | 未実行 | chunk前拒否 |

offsetはgardenを示す。正常strict6は支持2・不支持4（実行異常ではない）。故障判断1と期待契約拒否1を別に数える。retrieval hitがあっても完全spanなし、または根拠chunkが予算外なら支持false。overlapを増やすことだけを万能策にしない。

## 実行と記録

このdirectoryで `python3 -B runner.py --case overlap-budget-excluded`。fresh原票保存は明示 `python3 -B runner.py --record` のみ。採用原票はobservations/20261005T130618866255Z/raw.json、command exit0。UTC/runtime、3原文、固定span、fixture、chunk本文/範囲/score/完全span、rank/選択ID、重複/予算trace、6source SHAを保持。

`python3 -B check.py` はproducerをimportせず手書き範囲を照合し、原文offsetの独立countでunique/重複、残り容量からの予算表、検索hitの固定位置、各支持を照合。5種の意味ある改変を拒否。通常checkerとSkill routeは全ファイルhash/mtime不変、保存しない。

`python3 -B server.py` は専有127.0.0.1:0で同producerをUIから実行。case変更は3予測unknown、各予測単独変更は選択値保持。全run-startは同じclearを通して比較/表/trace/raw/答えを消し、generationで古い応答を破棄。拒否は工程未開始、EXECUTION_FAILUREはphase/error/未確認とし正常/不支持の答えを出さない。synthetic QA注入の返却失敗/HTTP503/保留応答は実外部障害と混同しない。

captureは実IABツール画面表示のみの場合、ローカル画像未保存とQAに明示する。再構成画像は作らない。sandbox bind失敗も保持して同一previewのhost許可でQAする。所有tab/portだけを終了する。

## 原典・実務判断・限界

2026-10-05に一次資料[OWASP RAG Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html) Section 3 Context Window Attacks、Section 5 Source Attribution and Provenanceを確認。取得chunkの量と由来/使用対象を追う観点へ接続する。仕様が本教材のoverlapやliteralルールを定義しているとは主張しない。生きた文書のlocatorで、文章/コードを転載していない。

実務ではどの文書/offsetが支持するか、索引に保持されたか、検索されたか、使用contextへ入ったか、重複費用を追う。独自ASCII/Python文字・単一chunk literal契約のみ。LLM/token数/embedding、意味的entailment/faithfulness、生成回答、prompt injection/poisoning耐性、ACL・tenant隔離、実製品RAGの安全性は未実証。全Core/fullGate、依存追加、設定変更、commit/push/公開/課金は未実施。Subject/Atlas全体の完成ではない。

## 次の未実施案

1. 同じspanで重複をoffsetで統合するcontext選択と現全chunk費用を比較する。順序/区切り費用も明記。OWASP Section3へ接続、現在はgreedy全chunkのみ。
2. 同じcitation/doc IDの別versionでoffsetとdigestを失効させる。古い原票の再使用を比較。OWASP Section5へ接続、現在は固定一version。
3. 多claimと一部欠落のliteral spanを追加し、全体拒否/部分表示/棄権を比較。元coverage claim-coverageとSection9 Output Validationへ接続。意味的言い換え/モデル生成は別実装が必要で、現在未実施。

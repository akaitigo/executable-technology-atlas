---
name: atlas-api-http-response-boundary
description: Atlasの有限HTTP応答を使い、JSONの文法、Content-Lengthの受信完了、本文上限を別々に判断する。
---

# Atlas：例外がなくても、本文の終わりを確かめる

[前提のHTTP契約](related.html?topic=api-readme)と[本文上限](related.html?topic=budget-readme)を読み、[今回の画面](index.html)、[契約](CONTRACT.md)、[手期待](expected.json)、[原典](SOURCES.md)、[範囲](COVERAGE.md)へ進む。実測は[保存結果](observations/run-01/results.json)の observations[].id と[実行時の判定実装](observations/run-01/inputs/boundary.py)へ結ぶ。計算・GUIの実施状態は[確認状態](qa/reader-acceptance.json)で確認する。expected.jsonは実装前の予測として残し、実測と区別する。

1. 「JSONを読めて例外なしなら完全か」には cases.id の `complete` と `short-content-length` を比較する。本文は同じ105byteだが、宣言105/106でframingの判断が分かれる。拒否した利用側はJSONを処理せず、decodedJSONはnull。isclosedは版に依存する補助観測で、一般的な完了判定に置き換えない。
2. 「完全受信したら上限も満たすか」には cases.id の `at-limit` と `over-limit` を比較する。8192/8193の両方で宣言長を満たす一方、後者は利用側の上限で止まる。これは既存budget原理の対照で、別の性能保証ではない。本文を切り詰めて有効な結果に見せない。
3. 「IncompleteReadが出なかったので再送は不要か、安全に再送できるか」には原典のread(amt)とread(None)の違いへ戻す。今回の情報だけで業務結果や再送安全性は判断しない。[既存の再送・応答喪失](related.html?topic=retry)へ案内する。TLS・認証・任意framing・一般障害診断は範囲外へ案内する。

この3問は保存資料を辿る有限利用確認であり、一般Agent評価ではない。本文型やHTTPの状態を業務成功と同一視せず、外部API・旧教材・共有計画を変更しない。

保存readerでは4応答と資料導線を実画面でも確認した。390pxの図・表は左右へ移動して読み、全列が同時に見えるものとして説明しない。原典リンクのGUI検査は外部通信を遮断した応答で、公式本文の読取はSOURCESの既存確認と分ける。最終受入は確認状態へ結ぶ。

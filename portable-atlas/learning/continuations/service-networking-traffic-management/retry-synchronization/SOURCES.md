# 原典と独自規約

2026-10-07に[Microsoft Retry pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/retry)のRetry strategies、Impact on performance、Idempotency本文を読みました。複数instanceの要求を時間に分散する設計、積極的すぎる再試行が混雑を悪化させる可能性、処理後の応答欠落と重複効果は原典側の論点です。

今回の4 client、ID順、容量1、1tick、固定delay列、予算12/5は教材独自です。固定列の差を実測したrandom jitterの優劣や推奨設定へ読み替えません。応答欠落は今回の模型外で、既存の再開判断へ戻します。

AWS Builders' Libraryの候補URLも1回開きましたが、移転先の本文が取得結果に無かったため根拠に採用していません。連続再試行や大きい取得はしていません。本文の大量複製はせず、locator・読取箇所と[前提ファイルのhash](sources.json)を保存します。

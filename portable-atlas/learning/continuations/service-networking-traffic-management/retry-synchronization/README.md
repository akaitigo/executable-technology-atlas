# Atlas：全員で再試行すると、また重なる？

4つのclientが同時に試行し、失敗したclientが同じ待ち時間で戻ると何が起きるでしょうか。容量1のserverへ向かう固定列を、同期・分散・偏り・共有予算の境界で比べます。**固定分散delayの有限比較**であり、実通信やrandom jitterの性能測定ではありません。

## 前提から操作へ

1. [前提](PREREQUISITES.md)で要求の開始/完了、追加retry数、全call予算を確認します。
2. [画面](index.html)で4条件の1つを選び、「4 client全員が成功するか」を予想します。
3. 保存した結果を開き、初回tick0、失敗完了tick1、再開tick2、その後の境界を前後ボタンで比べます。
4. [手追跡](HAND-CALCULATION.md)・[契約](CONTRACT.md)と[実装](model.py)、[原典](SOURCES.md)を読んで答えを開きます。[Skill](SKILL.md)は問いから該当箇所へ案内します。

clientは要求を送る側、attemptは初回も含む1回の試行、delayは失敗の完了から次の開始まで待つ仮想tick数です。受理容量1は1tickに開始できる成功処理の枠です。同時に来た残りをqueueへ入れる仕組みはありません。

## 何を比べるか

|条件|手計算の全call / 成功client|比べる判断|
|---|---|---|
|同期|9 / 3|失敗者がt2、t4に再び重なり、Dが追加retryを使い切る|
|分散|7 / 4|B/C/Dがt2/3/4に1件ずつ戻る。初回の4件集中は変わらない|
|偏り|9 / 4|最初のretryは重なるが、Dの最後の待機だけ長く、t7に終わる|
|同期・予算5|5 / 2|t2のB開始で予算が尽き、C/Dはretryを開始できない|

同じtickでは完了を先に観測し、次にID順でdueのclientを検査します。共有予算を先に消費できたものだけがserver枠へ進みます。追加retryの残数は予定した時でなく、開始した時に減ります。「予算でcallしなかった」と「callしたが過負荷だった」を分けます。

選択境界のclientカードはその時点までに観測した状態です。全試行表と図は最後まで保存した履歴なので、未来の完了結果も含みます。効果は成功完了で1件だけ増えます。今回の応答は失われないため重複効果0ですが、実処理の冪等性を証明しません。[結果不明からの再開](../agent-resume-uncertainty/README.md)へ戻ると別の問題を学べます。

## 保存と再現

計算を1回保存し、4条件の32tick・128client状態・30attemptを手表へ照合しました。17入力拒否と16保存改変の検出も確認済みです。4条件の全32tickを実画面で確認し、予想・条件・記録を変えた時の消去、読取拒否からの復帰、資料7件へのクリックも確認しました。1280/390幅の13画像と、その可視範囲は[実画面の確認記録](GUI-QA.md)へ分けて記載しています。[status.json](status.json)へ計算・画面・独立受入の現在状態を分けて記録します。[COVERAGE](COVERAGE.md)は契約時点の差分、[contract-lock.json](contract-lock.json)は実装前の8ファイルを固定した記録です。

計算はPython標準ライブラリのみで、`observe.py`が1つのJSONをstdoutへ出します。低優先度nice10、対象5秒以内の単一子として実行管理側が起動し、資源条件・終了・回収は別記録へ残します。新しい実通信、sleep、乱数、並列workerはありません。保存結果を確かめる [verify.py](verify.py) は計算を再実行しません。たとえば `python3 -B verify.py --result observations/result.json --report /tmp/atlas-retry-verification.json` で、元の[保存計算](observations/result.json)を上書きせず検査できます。最初の[検査結果](observations/verification.json)と[実行管理の記録](observations/root-run-reference.json)も分けて保存しています。

画面は保存JSONの再表示です。`python3 -B serve.py --port 0` でこのディレクトリだけをループバックへ静的配信できます。Markdown資料も文字として開けます。共有前提へのファイル参照は配信範囲外です。

この4条件から最適delay、確率的改善、実network/proxy/meshの性能、公平性・可用性・一般の副作用安全性は導けません。実務では失敗分類、期限、負荷、queue、冪等性などを併せて検討する必要があります。

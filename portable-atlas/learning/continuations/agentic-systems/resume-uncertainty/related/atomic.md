# 認証済IDのcheck/rememberのatomic性

公開fixture鍵でHMAC-SHA256を照合した2要求の受入を比較する有限教材です。同じ未登録IDでは、分離したcheck/writeの合法6順序中4順序が2件を受け入れます。check+rememberを1イベントにした2順序は1件です。集合seenが1要素でも受入が2回になり得ます。

`CONTRACT.md`の手表を先に固定し、独立した位置関係oracleで全56ケースを照合しました。実threadは別の14代表観測です。splitはcheck後Barrier、atomicはLock前Barrierで制御し、Lock内でcheck+rememberします。sleepを使わず、失敗とthread終了を記録します。意図的broken Barrierは成功に数えません。

## 実行

このディレクトリでPython標準ライブラリのみを使います。

```sh
python3 -B verify.py
python3 -B route.py
python3 -B serve.py
```

最後のコマンドが表示する自分のlocalhost URLを開きます。終了はそのプロセスにCtrl-C。第三者のサーバは操作しません。fixtureと順序を選び、二重受入を予測し、実行後のstepで要求ごとのcached_absent、受入数、seenを追います。「8順序を比較」は有限モデルを再計算します。「保存witness」は記録済の実thread観測を読み、threadを新たに起動しません。

## 証拠を読む

`observations/attempt-01/raw.json`は56モデルケース、23入力拒否、6mutant検出、実行環境と初回ソースhashを保存しています。`threads.json`は各fixtureのsplit/atomicを1回ずつ実行した生ログと意図的broken Barrier失敗です。`http.json`は実HTTP、`browser.json`は実UI操作で読んだ結果、`receipt.json`は凍結時の内容hash、`read-only-proof.json`は最後の読取検証の前後不変証拠です。rawを上書きしません。

独立oracleはproducerのイベントloopを呼ばず、check位置より前に受入writeが存在するかを判定します。HMACも別実装のSHA256 ipad/opadで照合します。これは暗号実装監査ではありません。実threadのwinnerやevent順序は固定していません。全6順序を実threadで観測したとは主張しません。実CPythonの観測を他runtimeのメモリモデル保証に一般化しません。

## 一次資料と版

- [Python threading: Lock / Barrier](https://docs.python.org/3/library/threading.html)。参照した現行文書はPython3.14.8。Lockがclassになったのは3.13で、それ以前はfactory。教材は共通の`threading.Lock()`、timeout付きacquire、Barrier wait/abortを使います。
- [Python3.9 threading](https://docs.python.org/3.9/library/threading.html)。参照文書は3.9.25、実行runtimeは観測記録の3.9.6。この2つを同版と扱いません。
- [RFC4303 §3.4.3–3.4.4](https://www.rfc-editor.org/rfc/rfc4303.html#section-3.4.3)。integrity検証成功前にanti-replay状態を更新しない関係を参照します。本教材はESP sliding windowを実装しません。
- [RFC2104 §2](https://www.rfc-editor.org/rfc/rfc2104.html#section-2)。独立MAC oracleのipad/opad構成を参照します。

## 限界

DB、永続化、TTL、再起動、分散処理、ESP実装、配送や副作用のexactly-once保証は対象外。公開鍵値は教材fixtureで秘密ではありません。ID/payloadのbyte表現自体を学ぶ既存教材は変更していません。ブラウザ画像は実captureですがファイル保存していません。有限単位の凍結候補であり、全Core auditとrepository gateはこの単位では実行していません。

制御失敗の実測は開始前abortのbroken Barrierだけです。Lock timeout・片worker例外・join期限到達は未実測で、cleanup構造は静的確認です。詳しくはCOVERAGE.mdを参照してください。

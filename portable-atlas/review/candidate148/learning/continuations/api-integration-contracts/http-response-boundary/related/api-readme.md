# HTTPの成功とJSON契約を分ける

標準ライブラリの実HTTPServerとHTTPConnectionを、自分の動的loopback portで接続する有限1教材です。固定合成JSONで12 GETを順次実行し、consumer契約の互換・拒否・エラー処理・timeoutを比較します。外部API・実認証・TLS・全HTTP仕様は未実証です。

## 今回の契約と観測範囲

[contract.json](contract.json)の成功は200＋application/json、必須id（integer≥1）とname（空でないstring）。noteはoptional string、追加fieldは許容。422はerror.code/messageを検査し業務エラーとして扱います。JSON Schema形式の固定定義を使いますが、[client.py](client.py)はその規則だけの手書き検査で、汎用JSON Schema validatorではありません。

| 比較case | 期待される処理 |
| --- | --- |
| base / optional＋extra追加 | item受入（2件） |
| 必須欠落 / id string化 / boolean id | schema拒否。型を黙って変換しない |
| 201 / text/plain | status / media拒否。201自体はHTTPの成功status |
| malformed / empty body | JSON構文拒否 |
| 422＋有効error / 422＋不正error | 業務エラー処理 / error schema拒否 |
| 応答前delay0.6秒 | client socket timeout0.1秒で停止、retry0 |

12 caseは互換2、処理済み業務エラー1、期待された拒否/timeout9です。これは観測runの合格とitem成功を分けた分類で、拒否を成功responseへ改変しません。optional追加の互換は追加field許容というconsumer方針に依存します。

JSONはUTF-8。media type本体を検査し、optional caseのcharset parameterは判定に使いません。application/jsonのcharset指定を必要条件や全media type共通規則として主張しません。レスポンス予算は8KiB（readは上限+1）、socket timeoutは通常2秒/遅延case0.1秒、観測subprocess全体15秒。socket timeoutは汎用end-to-end deadlineではなく、今回の遅延caseはheader前の待ちを検証します。body上限超過・途中切断はまだ実HTTPで試していません。

## 学習の道筋

1. **前提**：request/response、status/header/body、JSON値型。HTTPと業務データを別に読む。
2. **主要概念**：HTTPが成功でもschemaは保証されない。[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.3)のContent-Type/statusと、[RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html#section-3)の値型を確認する。
3. **今回実装・比較**：case選択→client処理を予想→request/response→status/media/JSON/schemaのstep→答え。baseとoptionalの互換、破壊的変更の拒否、422 errorとtimeoutを比べる。
4. **実務判断**：通信失敗、status不一致、media不一致、構文不正、必須/型不正、有効errorを区別する。201拒否はこのGETのexact 200契約で、HTTPの201一般を不正にしているのではない。timeoutからserverの未処理や安全な再送を推定しない。
5. **限界→原典/実装**：[case仕様](cases.json)、[実HTTP runner](experiment.py)、[client](client.py)、[独立case Oracle](verify.py)と[sources locator](sources.json)へ戻る。HTTPSや実APIの互換性は別環境で検証する。

### 次の問い・主要未教材（4実験とも未実施）

| 概念 | 次の有限実験案 / 問い | 公式locator |
| --- | --- | --- |
| retry / idempotency | POST処理後に応答を失い再送。二重更新を防ぐkey/記録と、methodのidempotencyを分けて検証。timeout後の再送は安全か？ | [RFC 9110 §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) |
| 標準error契約 | 今回custom errorとapplication/problem+jsonを比較し、status/bodyの矛盾を拒否する。エラーを機械処理できるか？ | [RFC 9457 §3](https://www.rfc-editor.org/rfc/rfc9457.html#section-3) |
| cache / conditional update | ETag/If-Matchでstale updateを止め、304/412の意味を区別。古いrepresentationで更新してよいか？ | [RFC 9110 §8.8](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.8)、§13 Preconditions |
| byte framing / deadline | UTF-8、分割応答、途中切断、8KiB境界を実serverで比較。部分bodyを完全なresponseとして受け入れないか？ | [HTTPResponse.read](https://docs.python.org/3.9/library/http.client.html#http.client.HTTPResponse.read)、[RFC 8259 §8.1](https://www.rfc-editor.org/rfc/rfc8259.html#section-8.1) |

認証/authorization/TLS、pagination・rate limit、webhook・非同期配送、API versioning/OpenAPI全検証、proxy/cache/HTTP2/3、外部API、SLO・負荷・production運用は別途未教材。これらを学ぶ際は製品/環境別の公式契約と実runtime検証が必要で、このloopback結果を一般化しません。

## 検査と再現

このdirectoryでPython 3.9以降・標準ライブラリのみ。通常のcheckerはnetwork/serverを使わず、保存原票をread-onlyで検査します。

```sh
python3 -B verify.py
python3 -B observe.py
python3 -B test_contract.py
```

原票更新を意図する時だけ、許可されたloopback bindが可能なterminalで実行：

```sh
python3 -B observe.py --write-evidence
```

自己所有serverを`127.0.0.1:0`へbindし、12 GETを1 attempt/retry0で実行。finallyでconnection/server/threadを終了し、port接続拒否を確認。独立検査器はclient/serverコードをimportせず、固定caseのstatus/header/body bytesと期待判定・gate列を照合します。実run＋Oracle全pass時だけstagingからdirectory renameで公開し、失敗は直前成功原票を保持、swap失敗はrollback。

request method/path・serverが実受信したheaders、response status/reason/headers/body hex・digest、elapsed、cleanupを`evidence/stdout.json`に保存。これはparsed HTTP観測とbodyの原bytesでありpacket captureではありません。実時刻/runtime/inputと14 source digestは`evidence/run.json`、全Artifact digest/bytesは`evidence/artifacts.json`。第三者本文/画像は保存せず一次資料locatorだけを持ちます。

## 画面

```sh
python3 -m http.server 0 --bind 127.0.0.1
```

表示された自分の動的portを開く。case→予想→step→原典/実装→答えを比較。保存原票再生でclientの新requestは発行しません。終了は自分のserverでCtrl-C。他担当listener/tabは操作しない。[QA](QA.md)、[coverage](COVERAGE.md)、[専用Skill](skills/atlas-api-integration-contracts/SKILL.md)を参照。分野全体の完成は主張しません。

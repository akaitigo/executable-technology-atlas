# Serverless Computing

local Python handlerの実行と、合成warm/cold再利用の有限教材。[index.html](index.html) で予想→操作→状態/result比較→原典/実装→答えへ進む。実cloud/課金function/cold-start wall clockは未測定。

## 学習の道筋

1. 前提: event、handler、mutable object、冪等性key。request用の値と再利用可能なclientを区別する。
2. 主要概念: environment寿命、request別scratch、(tenant,id)とpayload fingerprint、成功result cache、エラー時の未commit、store寿命。
3. 今回の実装: [events.json](events.json) の合成6eventを [model.py](model.py) のhandlerへ実関数呼び出しする。handlerはitemsのsum/countを返す。request用scratchを新規作成するprotectedと、environment共有listへ追加し続けるbadを比較する。
4. 正常/境界/異常: 空list、3要素、4要素拒否、key重複、異なるpayload競合、例外後再試行、cold時のstore消失を観察する。
5. 実務判断: warm再利用はevent dataを残してよい理由ではない。冪等性storeとscratch分離は別問題。process-local cacheだけでcoldや並行実行を越えた処理保証を主張しない。
6. 限界: cloudの実lifecycle、課金、外部storeの原子性、副作用とcommit後crashは未検証。下のcoverageへ進む。

## 実行

このディレクトリで標準ライブラリだけを使う。

```sh
python3 -B run.py
python3 -B run.py --reuse cold-each --lifetime process-local
python3 -B run.py --reuse cold-each --lifetime run-shared
python3 -B run.py --error handler-error
python3 -B run.py --payload conflict
python3 -B check.py
python3 -B server.py
```

serverが表示する127.0.0.1一時portを開く。所有serverはCtrl-Cで終了。専用UI/APIだけを配信。通常 [check.py](check.py) はread-only。原票更新は `python3 -B check.py --record` の明示optionのみ。未対応CLI入力はJSON rejected/exit2、HTTP400、UIは前回結果を消去。event個別の拒否/handler例外は正常な実験結果でHTTP200。

## 寿命と実装の仮定

| 対象 | この教材の実装/モデル | 保証しないこと |
|---|---|---|
| handler | 実Python関数呼び出し、無副作用のsum/count | cloud invoke、network配送 |
| cold | 新しいEnvironment objectを作りinitCountを増やす | process起動や実cold-start時間 |
| warm | 同じobjectを使い続ける | providerの再利用頻度や期間 |
| process-local store | cold object再生成ごとに新MemoryStore | 再起動後や別instanceでの冪等性 |
| run-shared store | 同じlocal runだけ全objectで同じMemoryStore | 外部DB/永続化、process終了後の保証 |
| cached client | 固定labelの合成client object | SDK接続、認証、性能 |

reuseはwarm / cold-each / recycle-pairs（2eventごと）。6eventの合成initCountは1/6/3。store lifetimeはprocess-local / run-shared。keyはtenant a/bとid e1/e2/e3、itemsは0–3要素の整数0..9、bool/floatは拒否。これらは教材独自のpayload境界でcloud quotaではない。

同key+同payloadの成功resultだけdeep copyして保存・返す。payloadが違えばconflict。エラーは保存しない。handler-errorはindex4でscratch追加後・store commit前に起こす合成例外。protectedのrequest scratchは破棄され、badの共有scratchは残る。失敗後の実副作用や「effectはcommitしたが応答喪失」は未モデル化。exactly-once保証ではない。

## 手計算と実務判断

| 条件 | 期待 | 判断 |
|---|---|---|
| warm/process-local/duplicates/normal/none | init1、handler4、duplicate2。protected sums 2,3,7,2,5,5 / bad 2,5,12,2,17,17 | b1にaの値が混入。duplicate result cacheも漏れを保持 |
| cold-each/process-local | init6、handler6、duplicate0。両variantのscratch漏れなし | storeが消えるので再実行 |
| cold-each/run-shared | init6、handler4、duplicate2 | 1run共有のモデルで抑制、外部永続保証ではない |
| warm/process-local/handler-error | index4 error、index5再実行。protected b2 sum5 / bad sum22 | error後の共有listに5が残り、再試行で再追加 |
| oversize | index1 input-rejected、handler未呼出 | 入力拒否はstore/scratchを変更しない |
| conflict | storeが残る場合index3 conflict | coldでstoreが消えたときは競合記憶も失われる |

履歴とraw stateを見ることで、単なるinit回数やhandler回数の一致だけでは分からない値の混入を検査できる。

## 独立oracleと原票

[oracle.py](oracle.py) はmodelをimportせず、fixtureを別定義し、prefix内の成功履歴とenvironment区分から結果・scratchを計算する。逐次handler/store実装とは別方法。checkerはbefore/after storeのpayload hashと保存resultも独立再構成し、120条件、手計算4条件、入力境界、意図故障を確認する。

[evidence/run.json](evidence/run.json) に全入力/event/実handler result、before-after scratch/store、独立期待、input/raw digest、実行時刻/環境を保存。[bindings](evidence/bindings.json) がsource/artifact digestと原典locatorを結ぶ。[UI QA](evidence/ui-qa.json) に実HTTP IAB操作/観測、captureの取得/保存可否、所有server/tabの終了を記録。[Skill](skills/atlas-serverless-computing/SKILL.md) は既存runner/checker/UIだけへroute。[routing-smoke](evidence/routing-smoke.json) は主agentの実確認で独立forwardAgentEvalではない。

Core `atlas audit` / `npm run gate` は専用module scope外で未実行。全Subject完成は主張しない。Goalは作成しない。

## 未教材coverageと次の実験

| 主要概念・問い | 次の実験 | 公式locator |
|---|---|---|
| trigger/delivery: 同期/非同期、queue/stream、batch、重複、DLQは | 合成batch部分失敗、再送とDLQを比較 | [AWS async errors](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html) |
| durability/concurrency: store TTL、同key競合、commit後応答喪失、副作用は | 合成atomic claim、commit crash、外部storeモデルを比較 | [AWS idempotent code](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) |
| runtime/scaling: init/invoke、concurrency、timeout、memory、観測/費用は | 合成arrivalとconcurrency capのqueue/latencyを比較 | [Lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)、[Reserved concurrency](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html) |
| identity/deployment: IAM、event権限、secret、version/alias、rollbackは | 合成resource権限表とversion切替/rollbackを比較 | [Lambda IAM](https://docs.aws.amazon.com/lambda/latest/dg/security-iam.html) |

以上は未教材。実cloud、外部永続store、課金function、cold-start時間、TLS、並行handler、deployment、実credentialは含まない。

## 原典と今回の対応

- [AWS Lambda best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) Function code: environment再利用とevent dataの分離、冪等性の原典。今回SDK接続やcloud invokeはない。
- [Runtime environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html): Init/Invoke等の原典。今回はobjectのinit counterのみ。
- [Async error handling](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html): retry・重複を考える原典。今回の配送順序やstore方針をAWS保証へ読み替えない。

公式ページを制作時に実取得確認。全文は複製しない。

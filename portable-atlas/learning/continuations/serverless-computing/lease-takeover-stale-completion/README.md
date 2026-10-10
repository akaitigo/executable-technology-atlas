# 未完了claimのlease引継ぎと遅れた完了

[元: store寿命](../../../subjects/serverless-computing/README.md) → [前: generation CAS](../../operational-data-stores/key-generation-cas/README.md) → このlease引継ぎ。成功commit後の[retry-idempotency再生](../../api-integration-contracts/retry-idempotency/README.md)に対し、未完了claimの期限・再取得・旧token完了という増分を扱う。既存Mac Python3.9.6/sqlite3だけ。

先に予想を選び、SQLiteで実行してrowcount/SQL/stateを追う。原典・実装・事前手表へ戻り、答えを開く。最後の操作tickを変えると実結果も答えも更新する。位置は下の選択操作だけ、答えは全trace終端。

|takeover操作|rowcount|直後state/owner/gen/expiry/result|
|---|---:|---|
|A t0 claim|1|IN_PROGRESS/A/1/10/null|
|B t9 claim|0|IN_PROGRESS/A/1/10/null|
|B t10 claim|1|IN_PROGRESS/B/2/20/null|
|B t11 complete 200|1|DONE/B/2/20/200|
|A t12 gen1 complete 100|0|DONE/B/2/20/200|
|同じ旧AをjobIDだけで故障更新|1|DONE/B/2/20/100|

lease10、tickは仮想整数0..20。sleepや実時刻による待機はない。claimはREADYか、IN_PROGRESSかつexpiry<=nowのrowをUPDATEし、ownerを変更、generationを+1、expiryをnow+10にする。completeはownerとgeneration、IN_PROGRESS、now<expiryを全てWHEREへ入れる。A t9完了は1、t10ちょうどは0。ownerだけ違い、generationだけ違い、DONE後の同tokenをそれぞれ独立条件にして0行を確認する。tokenはDBで今回のclaim時に発行する有限契約で、分散発行器ではない。

[SQLite UPDATE §2](https://www.sqlite.org/lang_update.html)はWHEREが真のrowを更新し、0rowはSQL errorではないと説明する。期限10やtoken条件は本教材独自の契約。故障版はjob_idだけをWHEREにし、DONE200を100で上書きする。

各操作は新しい接続でUPDATE→commit→close、観測は別read-only接続。専用TemporaryDirectoryに1case1DBを作って回収。明示record時だけclosed DBをattemptへ保存。通常checkerは専用tmpで実再計算し、保存DBはmode=ro&immutable=1/query_onlyで別SELECTを行う。

事前手表はproducer実装前に固定。独立oracleはrunner・SQL判定を共有せずliteral rowcount/state/tick表と別readonly SQLで検査。9条件25操作、generation欠落/unknownowner/bool/negative tick等7入力を操作SQL前に拒否。拒否操作はSQLなし、別observerのSELECTでstate保持を確認する。missing_jobsへの実SQLはOperationalError・rowcount=null。0行成功とは別。Python3.9 API未提供のerror code/nameはnullとし推測しない。

```sh
python3 -B verify.py --record attempt-01  # 未使用attemptのみ
python3 -B verify.py --seal-record       # UI QA後だけ
python3 -B verify.py                     # 実再計算、module保存なし
python3 -B route.py
python3 -B serve.py                      # 動的localhost、終了Ctrl-C
```

全可変入力で前結果と答えをreset。予想だけ変更すると新値を保持して本文を消し閉じる。位置拒否は表示と開いた答えを保持。SQL例外・host拒否は正常答えを出さない。旧応答はUI ticketで非採用。原票と初回receiptを保持し、QA後のcurrent bindingを別sealする。

実Lambda/実並行/時計同期/分散lease、lease expiry時の外部副作用停止、exactly-once、network partition、crash後復旧、負荷性能は未証明。tick編集は指定された有限逐次SQLの比較値で、実到着順を証明しない。次は同時claim、commit後応答喪失、外部effectのfencing（未実行）。元Subject・旧unit・共有Portalは編集せず、install・設定・公開・commit/push・Core gateは本専有制作の範囲外。

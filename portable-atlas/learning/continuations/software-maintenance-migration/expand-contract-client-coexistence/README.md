# 旧新clientを共存させるexpand/contract

前提はtransaction、SQLの列参照、金額の単位。[元教材の一transaction移行とrollback](../../../subjects/software-maintenance-migration/README.md) → この単元の `index.html` で予想・段階操作 → [独立手表と直接SQL](oracle.py) → [原典locator](sources.json) → 実用判断の順に読む。[release rollbackとdata互換性](../../../subjects/ci-cd-release-engineering/README.md) は旧artifactへ戻してもDBが戻る保証はないという関連の問いを提供する。

## 固定する契約と実際の動作

毎回専用 `:memory:` SQLiteを作る。既存DBや他owner資源は扱わない。3行の旧textは12.30、0.00、1.05。expandでnullableなINTEGER列を追加し、backfillで1230、0、105へ変換。旧clientのSELECTは旧列、新clientは新列を直接読む。追加だけでは新列はNULLで未移行である。

金額はASCII canonical文字列、小数2桁の0.00..9999.99、centは整数0..999999。Decimalで丸めず正確に変換する。01.20、1.005、指数、負数、全角、boolなどは拒否。bridge writeは同じtransactionのUPDATEで20.00と2000を更新する。故障は旧列だけ20.00へ更新し、1230との不一致を作る。

cutoverは全行の双方向金額一致と合成bool `retired=true` の両方を必要とする。これはclient廃止の入力契約で、現実のclient検出ではない。旧client稼働中は拒否。不一致は廃止=trueでも拒否。許可時だけ専用tableの旧列をDROP COLUMNする。contract後の新SELECTは成功し、旧SELECTは実際にOperationalErrorとなる。これは予定されたclient非互換観測であり、全実行失敗とは分ける。注入SQL故障はtransactionをrollbackしEXECUTION_FAILUREとして前比較と正常答えを消す。

## 再現と証拠

```sh
python3 -B verify.py
python3 -B route.py
python3 -B serve.py
```

画面は保存済み実DB観測の表示で、SQLを再実行しない。8条件、段階別schema・literal全行・client出力・guardを手表で照合する。oracleはproducerをimportせずlive DBへPRAGMA/SELECTを直接発行し、固定期待値に照合。traceには実BEGIN/UPDATE/COMMIT/ROLLBACKとclient SQLを保存。5金額の境界対、18不正入力、6結果改変も検証する。通常checker/routeは書かない。新規記録は明示 `--record attempt-02` 一回だけ。UI確認後のsealは初回receiptと生SQLを保ち、現sourceのreceiptを別に作る。

## 原典から判断する

[Parallel Change](https://martinfowler.com/bliki/ParallelChange.html)（Danilo Sato、2014-05-13、Martin Fowlerサイト）はexpandで新旧を併存させ、migrateで利用側を移し、contractで旧側を取り除く段階を説明する。本教材はこの考えを単一SQLite接続の合成clientへ限定して実行する。[SQLite ALTER TABLE](https://www.sqlite.org/lang_altertable.html) の§4/§5を列追加・削除に対応させる。依存view/trigger/indexのあるschemaはこのfixtureに含めない。

backfill完了だけで旧writerを止めずにcontractしてよいとは言えない。全行整合、旧client廃止、bridge更新の範囲を別に確認する。旧artifactへrollbackしても、contract後の旧SQLは失敗する。列復旧やbackup restoreは別計画が必要。本番同時writer、zero downtime、lock停止時間、長期backfill、電源断は未実証。SubjectやAtlas全体の完成は主張しない。

次は2接続writerの競合、batch backfillの中断・再開、contract後のbackup restoreを別々に検証する。

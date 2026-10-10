# 実行前の固定scheduleと期待

初期value0、更新1、assert期待1。同じ`assertBody`を全4正常契約caseで使用。variantはunawaited/await-completionのみ。scheduleはassert-before-update/update-before-assertのみ。unknownは実行前にexit2拒否し、work/test/assertを作らない。case IDはfixture固定選択、環境変数は明示variant/scheduleだけ。

| variant / schedule | assert時value | assertion / exit | 完了後value |
|---|---|---|---|
| unawaited / assert-before-update | 0 | fail / 1 | 1 |
| unawaited / update-before-assert | 1 | pass / 0 | 1 |
| await-completion / assert-before-update | 1 | pass / 0 | 1 |
| await-completion / update-before-assert | 1 | pass / 0 | 1 |
| unknown schedule | 対象なし | input refusal / 2 | 対象なし |

scheduleのbeforeはtestを先に開始する意味。await版はtest内のassert自体をcompletionまで待つため、実assertはupdate後へ移る。before unawaitedはtest完了後にupdate gateをreleaseする。afterはharnessがupdate完了を確認してからtest開始する。sleep/setTimeout/setImmediateで勝敗を誘導しない。

[独立literal表](oracle.json)へ各event順を固定。明示gateが更新をreleaseし、work Promiseが実completion signal。test登録のPromiseとwork Promiseを区別する。test wrapperに1行awaitを足す以外は同じassert body。failed assertionは実Node test runnerのnot ok/ERR_ASSERTION/exit1を保存し、expected反例とunexpected execution failureを分離する。cleanupではgateをreleaseし残るworkをsettle、所有childの終了を確認する。

正解は「待たない版は固定scheduleに依存してfail/pass、work完了をawaitする版は両scheduleでpass」。これは2schedule model、実OS競合・全flaky原因・時間分布の証明ではない。

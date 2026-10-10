# 非同期test: Promiseの完了を待ったか

[元Subjectの読む道筋 §6実験3](../../../subjects/software-quality-engineering/LEARNING_PATH.md#6-次の実験案3本すべて未実行)から進む有限追加単元。[行coverageと境界mutation](../../../subjects/software-quality-engineering/README.md)ではassertが仕様差を見抜くかを学び、ここではassertを**いつ**行ったかを実Node test runnerで比べる。

読む順番は前提→固定scheduleの予想→同じassert bodyの比較→実event/TAPと原典→答え/実務判断。前提はPromise、async/await、assert、0→1状態更新。[process context教材](../../observability-engineering/process-context-propagation/README.md)のprotocol順序と同じく、時計表示のsortと完了の依存関係は別。この単元は単一Node test file内の明示gateでありprocess間traceの実証ではない。

[事前期待](EXPECTATIONS.md)でvalue0→1、assert期待1、2variant×2scheduleを固定し、[手書きevent/value表](oracle.json)を実行前に作った。sleepやtimer長で勝敗を誘導しない。schedule beforeは「testを先に開始」、afterは「update完了後にtest開始」。await版beforeではtestが待機するため、実assert順はupdate後に移る。

| variant / schedule | 実assert value | assertion / outer exit | 最終value |
|---|---|---|---|
| 待たない / test先 | 0 | fail / 1 | 1 |
| 待たない / update先 | 1 | pass / 0 | 1 |
| work完了await / test先 | 1 | pass / 0 | 1 |
| work完了await / update先 | 1 | pass / 0 | 1 |
| unknown schedule | 対象なし | 入力拒否 / outer1・file2 | 対象なし |

[UI](index.html)で条件→予想→保存実測比較→event順/value/assert→原典/実装/raw→答えを辿る。条件変更で予想・結果・答えをreset。予想変更では新予想を保持して旧結果・答えだけを破棄。入力拒否時も予想と理由を比較する。browserは保存実Nodeログを再生し、Nodeや業務処理を実行しない。

[case.test.mjs](case.test.mjs)は全4caseで同じ`assertBody`を呼ぶ。workはupdateGateを待ち、release後にvalueを1へ更新する。work.thenの完了observerでwork_settledを記録。test wrapperの差はworkをawaitするかだけ。harnessはtestEntered gateを使い、before/unawaitedだけtest完了後にupdateをreleaseする。afterはharnessがwork完了を確認してからtestを開始する。この制御により2つの順序を時間待ちなしで再現する。test登録が返すdone Promiseと業務work Promiseを取り違えない。

[runner](runner.py)は同じsource bytesを所有private tempへコピーし、実`node --test --test-reporter=tap case.test.mjs`をspawn。生stdout/stderr/exit、outer PIDとtest file PID、parsed event、copy source SHA、child reap/stream close/temp cleanupを保存する。失敗TAPにもERR_ASSERTION/actual0/expected1を残し、passの再実行だけを残さない。[oracle](oracle.py)はproducerをimportせずliteral順/値と生TAPを照合する。

初回のunknown scheduleについてouter exit2予想は反証された。fileはexit2、Node --testはTAPのexitCode2とouter exit1で報告した。[初回記録](evidence/first-attempt.json)と[旧期待](evidence/first-oracle.json)を保全し、新期待で両exitを照合。初回生ログにworkspace絶対pathが入ったため原本をprivate tempにhash付きで保全した。以後はowned tempで実行し、生TAPにユーザーworkspace pathを含めない。work_settledをPromise完了observerへ改めた再実行でも旧runを上書きしない。

```sh
python3 -B runner.py                   # 保存current原票read-only
python3 -B checker.py                  # literal順/value/assert/TAP/source照合
python3 -B route.py completion
python3 -B route.py os-race            # unsupported exit2
python3 -B runner.py --record          # unique新原票、旧runと失敗保全
python3 -B checker.py --record-binding # 明示digest更新のみ
python3 -B preview.py                  # 所有dynamic127.0.0.1 preview
```

通常checker/routeはNodeを再実行せずfileを変更しない。独立追試はrunner.run()をメモリ内で実行しoracle.validateへ渡せる。expected assertion fail1、input refusal1（outer1/file2）、pass3とunexpected failureは別。所有子processは5秒watchdogで終了/reapし、そのtimeoutをschedule誘導に使わない。

答え: 待たない版は同じtest/bodyでもscheduleでfail/passが変わり、最終value1だけを後から見ても早過ぎたassertを見抜けない。work completionをawaitした版は両scheduleでassert1。failは教材の期待反例、scenario検算PASSはtest全件passを意味しない。

実務判断: sleepを増やす前に、assertが必要な処理の完了Promiseを待つかを確認する。待機をtest wrapperの返すPromiseに含め、失敗schedule・event順・assert時valueと完了後valueを保存する。今回の2scheduleだけから製品のflaky率や全原因を説明しない。

coverage増分は明示完了signalとasync test assertion順序。次の3実験（未実施）:

1. rejection時のawait/catchとunhandled rejectionを別caseで観測。[Node test runner](https://nodejs.org/download/release/v25.2.1/docs/api/test.html)
2. mock timerとPromise microtaskの依存を別fixtureで比較。同じvirtual時刻でも未完了を区別。[Node Timers](https://nodejs.org/download/release/v25.2.1/docs/api/test.html#timers)
3. async2処理のshared stateとtask-local contextを明示gateで比較。[process contextの前提教材](../../observability-engineering/process-context-propagation/README.md)

限界: 実Node v25.2.1・合成1test・固定2schedule、単一test file内Promise。実OS並行性、全flaky原因、時間分布/performance、mock timers、CI差、random scheduling、browser asyncは未実証。全Subject/Atlasや旧Gateを主張せず、他教材/Portal/既存serversを触らない。install/commit/push/公開なし。

[原典](SOURCES.md) · [fixture](fixture.json) · [current raw](evidence/current.json) · [binding](evidence/binding.json) · [実IAB QA](evidence/ui-qa.json) · [検証](evidence/verification.json) · [限定Skill](skills/atlas-async-completion/SKILL.md)

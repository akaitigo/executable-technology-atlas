# 200は返った。でもprocess境界でtraceはつながった？

[第1単元](../../../subjects/observability-engineering/README.md)の「関数内の親child binding」から、既存次実験のprocess contextへ進む有限追加単元。実Python childをcaseごとに起動し、stdin JSONを渡してstdoutを保存する。固定ID・独自carrierであり、OTel SDKやW3C適合試験ではない。

前提はprocess、stdin/stdout、JSON、trace ID/span ID/parent span ID。[事前契約](EXPECTATIONS.md)で型・ID・欠損・不正contextを固定し、[独立手書きID関係表](oracle.json)を実行前に作った。units2の業務結果は200と先に予測。

| 条件 | 業務結果 | child trace / parent | 観測品質 |
|---|---|---|---|
| propagated | 200 | 親と同じaaaa… / 親span bbbb… | 接続あり |
| missing | 200 | 別dddd… / null | orphan |
| trace-only | 200 | 親と同じaaaa… / null | orphan |
| upper-bound | 300 | 別dddd… / null | orphan |
| 型・欠損・不正context 6case | exit2拒否 | child spanなし | 対象なし |

[UI](index.html)は条件選択→予想→操作→業務/観測別欄→原典/実装/raw→答え。条件変更で以前の予想・結果・答えをresetする。予想のみの変更では新予想を保持し、旧比較・結果・protocol・答えを未比較へ戻す。拒否caseも予想と実理由を比べられ、拒否を成功業務や観測接続の成功として数えない。browserは保存された実processの結果を再生し、childをブラウザーから起動しない。

[runner](runner.py)は実Popen PID/親PID、送信stdin、正確なstdout2行、exit code、stderr、parent eventsを保存。[child](child.py)は実os.getpid/getppid、受信stdin、input、child events、計算結果とspanを出力する。第1行flush完了後のchildemit_completed ackを第2行に出す。parentはEOFまで読む。checkerは同じbytes、line順、同じPID/PPID、各process内seq、ID関係とliteral業務結果を独立に照合する。親child時刻は別配列で扱い、UTCを単純sortして因果関係を証明しない。parentwrite_completedの時刻がchildreadより前とは要求しない。protocolの順序とclock観測は別。

答え: 業務成功200だけでは伝播欠落を見抜けない。trace-onlyの同じtrace IDでも親spanがnullなら親接続を失う。scenario検算PASSは故障を含む予測どおりという意味で、observabilityの完全性PASSではない。

```sh
python3 -B runner.py                   # 保存current raw read-only
python3 -B checker.py                  # 独立oracle/source/raw/UI/binding照合
python3 -B route.py propagation
python3 -B route.py w3c                # unsupported exit2
python3 -B preview.py                  # 所有dynamic127.0.0.1 preview
python3 -B runner.py --record          # 明示新rawのみ。旧run保全
python3 -B checker.py --record-binding # 明示artifact digest更新のみ
```

通常checker/routeは再実行やfile変更をしない。独立追試は`runner.run()`をメモリ内で実行し`oracle.validate()`へ渡す。明示recordはUTC/UUID名で旧rawを上書きせず、unexpected execution failureもfailed原票へ残す。期待拒否exit2とunexpected failureは別。owned childは5秒timeout時kill/reapしstreamをcloseする。他processを停止しない。

実務判断: inject/extractをprocess境界の責務として明示し、trace IDとparent spanの両方を照合する。業務成功率、入力拒否、観測欠落を別に集計し、時刻表示だけで接続完全性を判定しない。独自carrierをそのまま製品標準として導入する根拠にはしない。

coverage増分は実processへの明示context、送受bytesとparent bindingの照合。次の3実験は未実施:

1. async2分岐でtask-local contextが混ざるかを固定入力で比較。[Context Propagation](https://opentelemetry.io/docs/concepts/context-propagation/)
2. 収集buffer容量3で停止/復旧時のdrop・duplicateを業務成功と分離。[Sampling](https://opentelemetry.io/docs/concepts/sampling/)
3. clock skewの合成表示で時刻sortとspan bindingが食い違う反例を比較。実分散clock精度の測定と区別。[Traces](https://opentelemetry.io/docs/concepts/signals/traces/)

限界: ローカル逐次child、固定case ID、stdlib、units1..3、custom JSON。実network、SDK、W3C、sampling/collector、分散clock、performance、実運用incidentは未実行。入力契約の全組合せ網羅も主張しない。Subject/Atlas全完成や旧Gateを主張せず、既存教材/Portal/serversは編集しない。

[原典](SOURCES.md) · [fixture](fixture.json) · [oracle](oracle.py) · [current raw](evidence/current.json) · [binding](evidence/binding.json) · [実IAB QA](evidence/ui-qa.json) · [検証](evidence/verification.json) · [限定Skill](skills/atlas-process-context/SKILL.md)

# Service Networking / Traffic Management

固定callableを実行する標準ライブラリのcircuit breaker/retry有限教材。[index.html](index.html) で予想→操作→traffic/状態/時刻比較→原典/実装→答えへ進む。壁時計を待たずvirtual timeだけを使う。実service mesh・TLS・network deliveryは未実行。

## 学習の道筋

1. 前提: request、失敗、deadline、待ち行列。到着時刻と実行開始時刻は異なる。
2. 主要概念: closed/open/half-open、failure threshold、cooldown、probe、bounded retry、backoff、共有call budget、deadlineの優先判定。
3. 今回の実装: [model.py](model.py) の固定callableとserial request simulator。8requestがtick0,2,…,14に到着。1callは1tick、開始tickが固定回復tick以上なら成功。callableをPython内で実呼び出しし、raw returnを保存する。ネットワークのrequestではない。
4. 正常/境界/異常: 回復後probe成功、回復しないprobe再失敗、deadline0/1、budget1/16、cooldown境界、retry0/2、悪い無制限retry方針を比較する。悪例も独立hard cap24callsで有限停止。
5. 実務判断: retryは故障を直さず、負荷や副作用を増やし得る。breaker、deadline、budget、冪等性、並行数、待ち行列、観測を一緒に設計する。
6. 限界と次の実験: この三状態モデルは実proxy/meshの完全再現ではない。下のcoverageから公式原典へ進む。

## 実行

このディレクトリでPython標準ライブラリのみ。

```sh
python3 -B run.py --threshold 2 --cooldown 3 --retries 1 --deadline 5 --budget 16 --recovery 8
python3 -B run.py --threshold 1 --deadline 1 --recovery never
python3 -B run.py --deadline 0
python3 -B run.py --budget 1
python3 -B check.py
python3 -B server.py
```

serverの表示する127.0.0.1の一時port URLを開き、所有serverをCtrl-Cで終了。専用UI/APIのみ配信。通常 [check.py](check.py) はread-only、原票更新だけ `python3 -B check.py --record` を明示する。CLIの未対応入力はJSON rejectedとexit2、HTTP400、UIは前回traceを消去して入力拒否。deadline/budget/openによる評価結果は正常な実験結果でHTTP200。

threshold整数1..3、cooldown整数1..4、retries整数0..2、deadline整数0..5、budget整数1..16。bool/floatは拒否。recoveryは4/8/neverの文字列のみ。秒や実時間への換算はしない。

## 状態・時間モデル

- closed: 連続失敗countがthreshold以上でopen。成功でcount=0。時間窓の失敗率は使わない。
- open: `now < openUntil` なら即拒否。境界 `now == openUntil` からhalf-openへ移る。
- half-open: serial処理なのでprobeは1つ。成功でclosed、失敗でopenしcooldownを再開始。deadline/budgetで呼べない場合はhalf-openに留まる。
- protected判定順: hard cap→open/cooldown→共有budget→deadline→call。deadlineは `arrival + deadline`、完了 `now+1 <= absoluteDeadline` のときだけ呼ぶ。待ち行列やbackoffの時間も消費する。
- retry: 最初のcallはretry数に含めない。失敗後、breakerが開いていなければ1,2tickの指数backoffを進め、最大retries回再試行。openをretryしない。拒否は失敗countを増やさない。
- budget: run全体の全callを数える。retryだけの割合budgetではない。requestごとに補充しない。
- 悪例: breaker/deadline/retries/budgetを無視、待ちなしで失敗をretryする方針。実際のループは独立hard cap24callで停止し、以後のrequestもhard-limit。無限実行はしない。

| 手計算条件 | 期待 | 判断 |
|---|---|---|
| default 2/3/1/5/16/recovery8 | protected6 / bad16 calls。tick3 open、6 half-open、7 open、10 half-open、11 closed | probe失敗から再probeで復帰 |
| threshold1/cooldown3/retries0/deadline1/budget16/never | protected4 / bad24 calls | callのfinishはdeadline境界で受理、probeも失敗 |
| deadline0 | protected0 | 1tickのcallが収まらない |
| budget1 | protected1 | 共有budget拒否はcallしない |

これらは教材方針の値で本番推奨設定ではない。Envoyのcircuit breakingはconnection/pending/active request/retry等のresource制限であり、本教材のアプリ三状態モデルと同一ではない。

## 独立oracle・実行証拠

[oracle.py](oracle.py) はmodel/callableをimportしない。requestごとに候補retry slotを先に列挙し、transition/timeを別計算する。悪例は回復tickまでの連続単位slot数を閉形式で計算する。checkerは実callable raw return、request開始/完了/outcome、状態/失敗count、transition時刻を照合し、手計算表とdeadline/budget/cooldown境界も検査する。

[evidence/run.json](evidence/run.json) に216条件の入力、全call raw return、retry-wait、request結果、transition、独立期待、input/raw digestと実行時刻/環境を保存。[bindings](evidence/bindings.json) がsource/artifact digestと原典locatorを結ぶ。[UI QA](evidence/ui-qa.json) は実HTTP IABの操作/観測、capture取得/保存可否、所有server/tab終了を記す。[Skill](skills/atlas-service-networking-traffic-management/SKILL.md) は既存runner/checker/UIだけへの限定route。[routing-smoke](evidence/routing-smoke.json) は主agentの実確認で、独立forwardAgentEvalではない。

Core `atlas audit` / `npm run gate` は専用module scope外で未実行。全Subject完成は主張しない。Goalは作成しない。

## 未教材coverageと次の実験

| 主要概念・問い | 次の実験 | 公式locator |
|---|---|---|
| routing/discovery/load balancing: endpoint、weight、health、zoneで何が変わるか | 複数合成endpointの重みと故障偏りを比較 | [Envoy load balancers](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers) |
| resilience/concurrency: retry budget、jitter、hedging、backpressure、冪等性は | 複数clientの同期retryとjitter、副作用重複を比較 | [Retry pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/retry)、[Envoy limits](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking) |
| protocol/identity: 接続、multiplexing、mTLS、証明書更新は | 合成connection poolとcredential期限を別モデルで比較 | [Envoy TLS](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/security/ssl) |
| observability/rollout: 成功率、latency、overflow、trace、canaryの判断は | 合成route切替とerror/latency指標、rollbackを比較 | [Envoy tracing](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/observability/tracing) |

以上は未教材。実service mesh/TLS/network、並行probe、distributed budget、random jitter、HTTP status分類、request cancellation、冪等な副作用、性能・安全・可用性保証は含まない。

## 原典と実装の対応

- [Microsoft Circuit Breaker](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker) Solution / Considerations: 三状態とprobeの設計。本教材は連続失敗・probe1callのみで、原典の時間窓や並行性は未実装。
- [Microsoft Retry](https://learn.microsoft.com/en-us/azure/architecture/patterns/retry) Retry strategies / Idempotency: retry上限/待ち/副作用の判断。本教材は副作用なし固定callable。
- [Envoy circuit breaking](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking): 実proxyのresource制限。教材の三状態と等しいとは主張しない。

制作時に公式ページを実取得確認。最初のEnvoy retry候補URLは取得失敗し、取得できたMicrosoft Retryを根拠に採用。全文を複製しない。

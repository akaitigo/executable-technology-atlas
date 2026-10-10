# Observability：成功したrequestのtraceはつながっているか

実際のローカルPython関数を計装し、structured logs・親child spans・request counterを比べる有限教材1単位です。分散backend、OpenTelemetry SDK、OTel仕様全体の適合試験は未実行。分野全体は未完成です。

## 学習の道筋

1. **前提**：関数呼出し、例外、JSON、集計。traceは1requestの仕事のつながり、spanは1操作の区間、logはevent、metricは複数requestの集計、として読み始めます。
2. **主要概念／仕組み**：requestがprice_lookupを呼び、成功200／固定LookupError503を返します。各requestは6log・2spans。logのtrace_id/span_idでどの操作かをたどり、childのparent_span_idで親へ繋ぎます。counterのlabelはroute=quoteとoutcome=success/errorだけ。高cardinalityになり得るrequest_idなど予期しないkeyを拒否します。これは教材の固定allowlistです。
3. **予想→操作→比較**：[UI](index.html)で予想を記入しsuccess/errorを実行。missing-propagationでは200・counter successでもchildのtraceが別、parentがnullとなります。error-orphanも比較。batchは成功2・エラー1、orphan1です。upper-boundはunits3で300、zero-units、unexpected-key/valueは実行前に拒否され、ログもcounterも増えません。拒否caseのbinding・duration検査は対象なしで、観測完全性の成功ではありません。rawのbindingCompleteはorphan検出ゼロの述語なので空集合でtrueになりますが、request0ならUIは対象なしと扱います。
4. **原典／実装→答え**：[runner.py](runner.py)は実関数を計装。[oracle.py](oracle.py)は独立した固定応答・event順序・counter規則、span区間の包含、実duration算術、log/span bindingを検査します。rawを見ると正常もorphanもlookupは実行済みです。答えは「成功counterだけではtrace伝播の欠落を見抜けない」。scenario検算PASSは、欠落を含む予想どおりの反例が記録された意味です。bindingComplete=falseなら観測品質は欠落しています。
5. **実務判断**：logsでevent、metricsで集計、tracesで呼出し関係を照合する。request IDはlogs/tracesで追い、counter labelへ無制限に入れない。span durationをUTC時刻の差で測らず、この教材では単一processのmonotonic clockを使います。timingと因果関係も区別し、時間内にchildが見えても親bindingがなければ完全なtraceと呼びません。
6. **限界**：固定trace/span IDは教材run内識別用で、複数runやサービスのglobal unique生成ではありません。single processの同期関数、固定入力、bounded label集合、メモリ集計。network伝播、並行性、clock skew、OTLP、semantic conventions、sampling、histogram、SLO/alert、retention、dashboard、実運用incidentは未実証。実timingは毎run変わり、この小関数のdurationから製品performanceを判断しません。
7. **原典**：[sources.json](sources.json)のlocatorと実装bindingからOpenTelemetry concepts、Python clock、Google SREへ進む。本実装を公式SDK／製品の実証と同一視しません。

## このMacで再現

このディレクトリでPython3.9以降、標準ライブラリだけ。

```sh
python3 -B runner.py --case missing-propagation
python3 -B checker.py
python3 -B checker.py --record
python3 -B server.py
```

checkerは通常read-only。保存rawはdigest・独立oracleで照合し、実関数の追試はメモリ内だけで検算します。時刻・durationの値が毎run変わるため新旧rawの数値同一性を要求しません。原票の更新は明示`--record`だけ。serverの動的127.0.0.1 URLでUIを開き、Ctrl-Cで終了。

[実行原票](observations/run.json)に時刻・環境・input・raw・source/artifact digestを保存。[実Browser QA](observations/qa.json)と[session/cleanup](observations/session.json)、[Skill](skills/atlas-observability-engineering/SKILL.md)を別に保持します。UIは実runnerの結果を描画し、別の業務計算式を持ちません。

## 未教材coverageと次の問い

| 主要範囲 | 今回から判断できること／残る問い | 次の実験（未実施） | 公式locator |
| --- | --- | --- | --- |
| 分散traceとcontext | log/span bindingを追える。process境界と非同期taskでcontextをどう渡す？ | 2processの架空requestで伝播あり／なし、async分岐を比較。clock skewと因果bindingを分離 | [Context Propagation](https://opentelemetry.io/docs/concepts/context-propagation/) / Manual propagation、[Traces](https://opentelemetry.io/docs/concepts/signals/traces/) / Links |
| metrics・SLI/SLO・alert | 固定counterと高cardinality key拒否を判断できる。latency分布やerror budgetをどう扱う？ | 固定100requestのhistogram・成功率をwindowで比較し、単発errorと持続burnを別alertへ | [Metrics](https://opentelemetry.io/docs/concepts/signals/metrics/) / Histogram、[Google SRE SLO](https://sre.google/sre-book/service-level-objectives/) / Indicators・Objectives |
| 収集pipeline・保持・費用 | raw evidenceを検算できる。export欠落・backpressure・再送・samplingは？ | buffer容量3の収集先停止と復旧、duplicateとdropを比較。head/tail samplingの偏りを測る | [Collector](https://opentelemetry.io/docs/collector/) / Processors・Exporters、[Sampling](https://opentelemetry.io/docs/concepts/sampling/) / Head・Tail |
| 診断・dashboard・運用とprivacy | response成功と観測完全性を分けられる。障害時にどのsignalから調べ、何を記録しない？ | 架空incidentをlogs→metric→traceで調査、原因候補と不足証拠を記録し機密fieldをredact | [Logs](https://opentelemetry.io/docs/concepts/signals/logs/) / Correlation、[SRE Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/) / Four Golden Signals |

まず親bindingの欠落を見抜き、分散伝播、集計とSLO、収集pipeline、診断へ進みます。この4実験は次の学習候補であり現在の実証ではありません。

# global minを待つ窓、maxが先に閉じる窓

[元Event Streaming / CDC](../../../subjects/event-streaming-cdc/README.md) E3の未教材watermark/windowから、固定2partitionの有限event-timeだけを追加します。SQLite outboxのcommit/checkpointとは別の時間・窓の問いです。

## 前提 → 予想 → 操作

前提は整数timestamp、到着順、max/min、半開区間、sum。元outboxの保存境界→このevent-time窓→idle判定・join/state/checkpoint・実Flink（未制作）の順で読む。

~~~sh
python3 -B runner.py --record
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py inspect
python3 -B route.py lesson
python3 -B preview.py
~~~

previewの127.0.0.1動的URLを開く。窓0のfinal sum（openならopen）、最終WM（未観測partitionならbottom）、drop数を予想→実子processで比較→原典/実装/raw→答え。到着配列の順・時刻・lag L・allowedLateness AをJSONで編集し、実処理し直す。各窓sum/ID/close step、trace、答えは新入力の実結果へ追従する。

## 固定した整数tick契約

- partitionはp0/p1、window幅10、time/valueは整数0..100、event数1..12、ID一意。LとAは整数0..20。未知mode/idle-autoは拒否。
- 各partition maxSeenは実到着の最大time。partitionWM=maxSeen−L。未観測partitionはbottom。globalは両partitionWMのminで単調。故障版maxは観測済みpartitionのmaxを使い、未観測や遅いpartitionを無視する。
- 窓は[start,end)。eventは **到着前のglobalWM** がend+A以上ならDROP_FINALIZED、それ未満かbottomなら受理。late判定はtime<到着前WM。受理後はmaxSeen/WMを更新する。
- 到着後WM≥endで初回fire。A>0ならstateを保持し、late受理が初回fire後なら更新fire。WM≥end+Aでfinalizeし、以後その窓へ入れない。表示は検証用archiveを保持するが、閉じた窓のsumは変えない。
- 有限input末尾に無限大watermarkを追加しない。片側停止/未観測はopenのまま。idle判定やwall-clock timeoutはない。

Flinkの概念に対応する教育モデルです。exclusive-endの整数tick cutとしてWMを定義し、Flinkのmillisecond maxTimestamp=end−1 timerやbounded generatorの−1まで同一再現とは扱いません。Lはwatermarkの遅れ、Aは初回fire後のstate保持期間で別パラメータ。Lを置いただけで未来の順序を保証しません。

## 事前literal → 正常/故障 → 答え

| 条件 | WM timeline | 窓0 / drop | 観測する境界 |
|---|---|---|---|
| min-complete L2/A0 | bottom,−1,−1,6,18 | sum7 final step5 / [] | p0が20でもp1を待ち、e4(time8,value4)を受理 |
| max-fault 同入力 | 0,0,18,18,18 | sum3 final step3 / [e4] | p0の進捗で早期close、minなら受理した4を失う |
| stalled-partition | bottom,−1,−1 | sum3 open / [] | p0だけ20へ進んでもp1 time1が止める |
| unseen-partition | bottom,bottom | sum1 open / [] | p1未観測を勝手にidle扱いしない |
| grace L0/A3 | bottom,2,2,10,10,10,13 | sum8 final step7 / [] | WM10で初回sum3、time9/value5をlate受理しsum8へ更新、WM13でfinal |
| deadline-boundary | 上記後13 | sum8 / [e8] | WM=end+A=13に等しい時点でtime9はdrop |
| no-grace-boundary A0 | bottom,2,2,10,10 | sum3 final step4 / [e5] | time10は窓[10,20)、WM10で[0,10)がclose |

[事前表](oracle.json)に各到着WM、受理/drop/late IDs、窓sum/ID/fire/final stepをproducerより先に固定。L0、到着順交換、L内out-of-orderも検算します。[model](model.py)はstateを逐次更新。[checker](checker.py)はproducerをimportせず、各prefixからmaxSeenと受理済み集合の窓を再構築する別経路＋literalで照合。max版のdropをmin基準の受理IDsと別比較する。

[execute](execute.py)は毎回実model子processと独立audit子processを起動し、input/argv/UTC/exit/stdout/stderr/sourceHashesを返す。UI JSでwindow計算を代算しません。拒否はREFUSED/exit2、JSON破損は実decode EXECUTION_FAILURE/exit3/stdout空。audit失敗/HTTP失敗/旧応答破棄も正常窓とは分ける。

recordだけが新UTC runとCURRENTを作り、旧rawを上書きしません。default runner/checker/inspect/lessonは全module SHA/mtime不変。UIはメモリreceiptを表示するだけで原票へ書かず、入力上限30000byte。条件変更は予想も空。入力/予想変更は新値を保持し旧status/窓/trace/答え/rawを空にしてdetailsを閉じる。世代違いの旧非同期応答は破棄。qaDelay=2000は応答transportだけ2秒保留するQA用で、model/audit時刻は実子process直前直後です。[QA](QA.json)に実IAB/capture/検証/資源終了。

## 一次資料 → 今回の実装範囲

[Flink Timely Stream Processing](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/)のevent-timeと複数inputのmin、[Generating Watermarks](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/event-time/generating_watermarks/)のout-of-order/idle、[Windows Allowed Lateness](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/)のstate保持を概念対応に限定します。ページ確認時のstableはv2.3.0、実行はMac Python標準ライブラリでFlink未install/未実行。

実Flink、無限stream、idle自動判定、periodic watermark emission、join/keyed state/checkpoint/savepoint/backpressure、実CDC/network、production completeness/durability/exactly-onceは未実証。[COVERAGE](COVERAGE.md)。旧unit/Portal/shared DB/settings/Core/fullGate/install/commit/push/公開は触りません。全Subject完成を主張しません。

# Workflowとbatch orchestrationを学ぶ道筋

この文書は[有限DAGの既存教材](README.md)から、依存、retry、並行性、再実行時の副作用へ進むための補足です。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と仕組み

有向graph、cycle、topological order、状態遷移、純粋関数と副作用を理解します。taskの定義、特定入力でのrun、run内の各attemptを分けます。dependencyの存在だけでは、先行taskの成功やartifactの有効性は保証されません。

学ぶ順序は **DAGと入力 → ready条件 → task state → retry予算 → 並行実行と資源 → artifact・再利用 → 副作用・復旧 → data intervalとscheduler** です。

- topological orderは一意とは限りません。複数の有効順があることと、runnerが並列実行することは別です。
- retriesは再試行数で、最大attemptはretries+1です。runを新しくすると予算が再設定されます。
- retrying、最終failed、下流blocked、cycleによるrun拒否を分けます。
- 同じ入力・実装のpure結果を再利用できても、外部効果のexactly-onceやcrash後の復旧は証明できません。

## 2. 予想から既存実測へ

[UI](index.html)、[runner](runner.py)、[最終checker原票](observations/checks-bc217609926242cdaeb6fafc12d185da/result.json)、[そのmetadata](observations/checks-bc217609926242cdaeb6fafc12d185da/metadata.json)、[QA](QA.md)を読みます。この文書作成ではrunner、checker、server、UIを実行していません。

seed2のDAGはA→B、A→C、B/C→Dで、A=2、B=4、C=5、D=9です。

| 条件 | 保存済み結果 | 予想との比較 |
|---|---|---|
| normal | 全task succeeded、主run呼出し4 | 有効順に依存を満たす |
| Bが一度失敗、retry1 | B attempt2で回復、D=9 | 最初の失敗だけでDをblockedにしない |
| Bが常に失敗、retry1 | B failed/attempt2、C成功、D blocked/attempt0 | 独立siblingは進むが依存先は動かない |
| cycle | task呼出し0、全task pending、run rejected | 実行前にgraph全体を拒否 |
| 同plan/sourceの成功再利用 | 主run attempt0・呼出し0、同じ値 | 既存pure結果の保持 |

初回失敗直後のDはpendingで、Bの最終失敗後のblockedと違います。24 permutations中の有効順は2つですが、逐次runnerはA,B,C,Dを選びます。12検査内の36条件照合は有限fixtureの結果であり、全workflowの証明ではありません。

入力を変えた再利用は拒否され、旧結果を保持します。UIの比較表は別のpure runを計算するため、主run呼出し0を画面全体の無計算と読みません。QAは過去版のchecker原票を歴史記録として区別しています。保存のstaging障害検査は電源断や分散storage耐久性の測定ではありません。

## 3. 実務で何を判断するか

先行成功だけで十分か、skipやbranchを許すか、何をartifactの有効性とするかを決めます。retryは一時失敗にだけ有効な場合があり、入力誤りや権限不足を上限まで繰り返しても回復するとは限りません。最大attempt、待ち時間、deadline、timeout、cancelをそれぞれ定義します。

再実行するbatchは対象data interval、入力版、task実装版を固定します。外部書込みがあるなら、安定した業務key、重複拒否やupsertの契約、commit後に応答を失った場合を検査します。成功結果の保存と業務効果のcommitは別の境界です。製品導入にはqueue・worker・権限・監視・容量の別検証が必要です。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [Python graphlib 3.9](https://docs.python.org/3.9/library/graphlib.html)、TopologicalSorter / prepare / get_ready / done / CycleError | 順序とcycle、readyと完了の分離。既存runnerは独自実装 |
| [Airflow 3.3.2 Tasks](https://airflow.apache.org/docs/apache-airflow/3.3.2/core-concepts/tasks.html)、Relationships / Task Instances / Timeouts / Retry Policies | 製品の状態、依存、attempt timeout、retryの比較 |
| [Airflow 3.3.2 Best Practices](https://airflow.apache.org/docs/apache-airflow/3.3.2/best-practices.html)、Writing a Dag → Creating a task / Communication | 再実行の同じ結果、固定partition、worker間のartifact共有 |
| [Airflow 3.3.2 Dag Runs（取得候補）](https://airflow.apache.org/docs/apache-airflow/3.3.2/core-concepts/dag-run.html) | interval/catchup/backfillの次の読解候補。今回は本文取得不能 |

Python公開資料は3.9.25で、既存runtimeは3.9.6です。Airflowのstate・機能と独自runnerを同一視せず、互換性や製品起動の証拠とは扱いません。

## 5. 未教材の問いと次実験

| 未教材 | 問い | 次の入口 |
|---|---|---|
| 並行・分散実行、resource pool | readyなsiblingが同時に進んでも依存と容量を守れるか | 実験1 |
| retry delay/backoff/timeout/cancel | いつ再試行し、何を最終失敗とするか | 実験2 |
| 副作用、idempotency、crash復旧 | commit後の応答喪失で効果が重複しないか | 実験3 |
| interval、backfill、入力版とlineage | 過去区間の再実行で違う入力を読まないか | 実験4 |
| calendar・timezone・scheduler | schedule時刻と処理対象区間はどう違うか | Dag Runsの本文確認と別教材が必要 |
| branching、trigger rule、dynamic mapping | skip・分岐・動的task数をどう評価するか | 製品原典と別modelが必要 |
| 永続queue/worker、checkpoint、HA | worker消失や重複配送から何を回復するか | 実製品・storageの別検証が必要 |
| security、secrets、artifact store、運用 | 誰が実行・閲覧でき、失敗と容量をどう監視するか | 今回のpure整数taskでは未評価 |

## 6. 次の実験案（4本、すべて未実行）

1. **ready taskと容量制限を仮想時計で比較する。** A/B/C/Dに固定durationを与え、worker容量1と2の独自scheduler modelを比較します。予想は容量2ではB/Cが重なり得てもDは両方の成功後にだけ開始することです。start/end/active数を保存し、全edgeの先行完了条件、active数≤容量、最終値を手書きscheduleと照合します。異常版はBがまだrunningなのにDを開始させます。原典はgraphlibのget_ready/doneです。仮想時刻の短縮を実並列性能やthread安全性の測定にしません。

2. **retryの時刻と失敗分類を分ける。** 仮想時刻で一時失敗、永続失敗、durationが上限を超えるtaskを固定し、retry0/1/2と固定delay・指数delayを比較します。予想は上限内の一時失敗だけが回復し、待機やtimeoutで開始時刻と最終stateが変わることです。独自の再試行対象例外、期限以上で失敗する境界、delay式を先に定義して、attempt別start/end/error、予算、下流stateを手書き表へ照合します。原典はAirflow TasksのTimeouts / Retry Policiesですが、製品のsensor等の全契約は実装しません。sleepは不要なmodel案です。

3. **副作用commit後の応答喪失を比較する。** 使い捨てのローカルledger modelに合成の業務keyと書込みを置き、「効果をcommitした直後、成功通知前に故障」をstateとして注入します。予想は無条件append版ではretryで2件になり、同じ安定keyを照合する版では1件を保持することです。業務効果の件数とrunnerのattemptを別々に保存し、key衝突・同key別payloadの拒否も期待表へ照合します。原典はBest PracticesのCreating a taskです。実外部API、実process kill、電源断、複数worker transactionのexactly-once保証にはしません。

4. **区間と入力版を再利用keyへ含める。** 合成の日別入力を2区間、各2版用意し、同taskでも対象区間・入力digestが変われば別結果になる契約を作ります。「latest」を読む故障版と、区間・版を固定する版を比較し、再実行前後で入力が更新された条件を手書き集計へ照合します。予想は固定版なら同じ結果を再現し、区間や入力版をkeyから落とすと誤った再利用が起きることです。原典はBest Practicesの固定partitionと`data_interval_start`の説明です。calendar schedulerやAirflowのbackfillを実行する案ではなく、Dag Runs本文の確認は製品機能へ広げる前の未完了条件として残します。

## 7. 資料の取得・検証状況

2026-10-05にPython graphlib、Airflow 3.3.2 Tasks / Best PracticesのHTML本文を取得して参照箇所を確認しました。Dag Runsの上記URLは2回ともInternal Errorで本文を確認できませんでした。URLの不存在や機能非対応とは判断せず、本文取得済み資料と区別しています。第三者本文・図・code exampleは保存していません。

追加したのはこの文書だけです。runner、checker、server、UI、global gateは実行せず、既存原票・QA・digestを更新していません。次実験の予想は新たな実測証拠ではありません。

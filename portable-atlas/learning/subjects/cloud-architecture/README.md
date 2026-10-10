# Cloud architecture：appを2zoneに置けば、依存の故障にも耐えるか

Subjectの入口です。今回の有限教材はstdlibの架空2zone service graphを実際に評価し、全故障matrixを生成します。実cloud・resource・製品設定・価格・SLA実測は未実行。全Subject未完成です。

## 前提 → 主要概念と仕組み

前提はgraph、AND/OR、確率、故障domainです。zone-a/b、app-a/b、dep-a/b、routerの7故障変数を扱います。zone故障はそのzoneのappとdepを同時に停止。routerは共通で、失敗すれば全routeが止まります。

|模型|routeと必要条件|依存の意味|
|---|---|---|
|shared|router → app-a/b → dep-a|共通dep-aはzone-aにあり、app-bも依存|
|local|router → app-a → dep-a、router → app-b → dep-b|各zoneに独立したread依存。両方に同じ対象dataがあると仮定|
|replicated|各app → dep-aまたはdep-b|複製は既に完了し、どちらからも同じreadが可能と仮定|

local/replicatedは同じ対象readをどちらの経路でも処理できる架空モデルです。実DBのwriter、同期、quorum、lag、整合性、failover手順を実装していません。bulkheadの独立cellとも同一ではありません。

成功routeは全nodeがhealthy。app・depのzoneもhealthyである必要があります。利用可能routeの中からlatency最小、同値なら辞書順を選びます。router1+app2+dep4=7synthetic単位、cross-zoneは+5で12。これは設定したcostの加算で、msや実network latencyではありません。runnerのexecutionObservedNsはローカル計算時間でservice latencyと無関係です。

## 予想 → 操作 → 正常・境界・意図異常を比較

「dep-a故障時にapp-bが生きていればsharedは動くか」を予想し[UI](index.html)で操作します。

```sh
python3 -B runner.py --case dep-a
python3 -B server.py
```

表示された127.0.0.1動的portを開きます。diagramのedge・node状態とpathのblockedNodes、全128故障matrixを比較してください。

|case|shared / local / replicatedのserviceUp|理解する問い|
|---|---|---|
|healthy|true / true / true|latency設定7、正常route|
|dep-a / zone-a|false / true / true|app2台でも共通依存/zone故障が両routeを停止|
|app-a|true / true / true|shared app-bからdep-aへのcross-zone cost12|
|router / both-zones / all-failed|false / false / false|共通依存・全domain停止の境界|
|split-fault（app-a+dep-b）|true / false / true|replicatedではapp-b→dep-aが可能、localではroute無し|
|unknown-fault / duplicate-fault|拒否|曖昧な故障入力を成功扱いしない|

## 原典 → 実装 → 答え

[REL10-BP01](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_multiaz_region_system.html)と[REL10-BP03](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_use_bulkhead.html)で故障domainと共有依存を読み、[架空graph](architectures.json) → [runner](runner.py)のpath列挙 → [独立oracle](oracle.py)の固定route/Boolean式へ戻ります。答えはdep-a停止でsharedの両app経路が失敗する、です。

7bitの全128状態×3構成=384評価を検証します。成功状態数はshared10、local15、replicated17ですが、状態を等しく数えた比率は可用性ではありません。各故障変数のup確率を架空99/100・相互独立と仮定した場合だけ、Fractionで重みを合計します。zoneによるnode故障の相関はgraphに含めますが、7変数同士の現実の相関は含めません。[Availability Table](https://sre.google/sre-book/availability-table/)の時間可用性やSLAと、この瞬間の仮定付き確率を同一視しないでください。

oracleはrunner/graphをimportせず、固定routeとBoolean式、128状態の手計算集計値10/15/17、確率多項式を照合します。rawには仮定、path、health、selected route、入力と実行UTC/環境・digestを保存します。

```sh
python3 -B checker.py --record  # 明示更新：case/matrixの実行原票
python3 -B checker.py           # 保存原票・oracle・source/hash・QAをread-only検査
```

[実行原票](observations/run.json)、[QA](observations/qa.json)、[session](observations/session.json)、[sources/locator/binding](sources.json)、[module skill](skills/atlas-cloud-architecture/SKILL.md)。保存更新は明示optionだけです。

## 実務判断 → 限界 → 次に学ぶ

この入力で、どの共通node/domainがrouteを止めるか、複数zone配置が依存まで分離されているかを判断できます。実architectureレビューで依存とfailure boundaryを描く視点を得られます。現実のavailability目標、容量、復旧時間、latency、費用は決められません。

二値状態・瞬時router切替・完了済みread複製・容量無限の固定模型です。network partition、DNS、control plane、retry、timeout、write整合性、security、性能分布・cost/sustainabilityは未実証です。

|未教材coverage・問い|次の実験（すべて未実施）|公式locator|
|---|---|---|
|Reliability / data：partition・lag・quorumでread/writeはどう変わるか|架空2storeに遅延writeとpartitionを入れてstale readと切替を比較|[REL10-BP01](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_multiaz_region_system.html)、[REL05-BP01](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html)|
|Performance / cost / sustainability：zone冗長化の容量・費用tradeoffは何か|架空負荷・queue・resource単位を変え、待ち時間とcapacity/cost模型を比較。実価格なし|[Six pillars](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html)、[Cost pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)|
|Security / networking：identityと通信境界はroute可否へどう影響するか|架空policyでrole・network許可を変え、到達可能と許可済みを分ける|[Security pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)|
|Operations / validation：故障検知・切替・復旧の時間はどう観測するか|専用local processで停止→再開を実行、hypothesisとguardrail・観測値を記録|[REL12-BP04](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_testing_resiliency_failure_injection_resiliency.html)|

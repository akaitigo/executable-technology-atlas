# 重み付き選択とhealth再正規化

元[Service Networking Subject](../../../subjects/service-networking-traffic-management/README.md)のrouting/load balancing未教材から、整数bucketの選択だけを追加する。既存breaker/retryは実行しない。[UI](index.html)で予想→条件編集→実Python選択→正常/拒否/故障→一次資料/実装/実raw→答えへ進む。

## 実装と手表

候補A/B順、weightは整数0..4（bool不可）、healthはbool。健康かつ正重みの候補を先に絞り、半開区間の累積境界を作る。slotは整数 `[0,total)`、allなら全slotを順に列挙。各slotを実selectorへ渡して選択先/health/outcomeを記録する。候補が空ならREFUSED。故障版は正重みだけでbucketを作り、選択後にhealthを調べ、unhealthyをLOSSにする。retryや再選択は行わない。

| 条件 | 境界 | 全slot選択/結果 |
|---|---|---|
| A1/B3とも健康 | A[0,1), B[1,4) | A,B,B,B、成功件数A1/B3 |
| B unhealthy | A[0,1) | A、total1へ再正規化 |
| A0またはA unhealthy、B3 | B[0,3) | B,B,B |
| 選択後health故障でB unhealthy | A[0,1), B[1,4) | A成功、Bの3slotはLOSS |
| 全unhealthy/全zero | 候補なし | REFUSED |

事前[literal手表](hand-oracle.json)の15条件には負/小数/bool weight、slot負/total外/小数/bool、実RuntimeErrorも含む。slot0,last3,total4、およびB unhealthyのslot0,total1を照合。実例外はselector内でRuntimeErrorを発生させる有限fixtureで、実サービスの障害ではない。通信失敗はUIのTRANSPORT_FAILURE、入力拒否と実例外とは別に扱う。slot全列挙の比率は無作為trafficの測定ではない。

## 再現

Python既存標準ライブラリのみ。インストール不要。

```sh
python3 -B runner.py normal
python3 -B runner.py b-down
python3 -B runner.py late-health-fault
python3 -B verify.py
python3 -B route.py
python3 -B serve.py
```

serverが示す127.0.0.1の一時portを開き、所有serverだけCtrl-Cで終了する。通常verify/routeはmoduleへ書かない。初回原票記録は未使用attemptに `python3 -B verify.py --record attempt-01`、UI QA確定後sealを一度行う。既存原票を上書きしない。

[独立oracle](oracle.py)はproducerをimportせず、bucket構築やhealth predicateを再利用せず、事前literal全slot表と実trace/候補/境界/拒否を照合する。6mutantは誤slot、dead候補、誤境界、LOSS隠蔽、拒否/失敗の成功偽装を拒否。UTC・Python/OS環境・source/raw digestを保存。[Skill](skills/weighted-selection/SKILL.md)はこの教材だけへのroute。

## 原典と境界

[Envoy Supported load balancers / Weighted round robin](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers#weighted-round-robin)は、host選択のpolicy、endpoint weightが選択頻度へ影響することを説明する。制作時に実取得したlatest文書は1.40.0-dev。ここでは固定整数bucketを用いる独自教材で、Envoyのround-robin scheduleやhealth policyを再現したという主張はしない。healthは利用者が指定するboolで、実probeではない。

未教材: discovery、priority/panic、zone/locality、slow start、接続/実request、動的weight、latency、random traffic、並行状態、実Envoy/network、実サービス安全性・可用性。次はzoneとpriorityの固定候補集合、health観測の遅延を独立実験にする。Original97、Core/Portal/共有docsは変更しない。Core audit/full gateは専有範囲外で未実行、Atlas全体の完成は主張しない。

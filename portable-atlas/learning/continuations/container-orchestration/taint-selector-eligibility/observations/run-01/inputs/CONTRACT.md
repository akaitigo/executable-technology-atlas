# Atlas｜空きがあるのに、なぜ配置できない？

目標47の配置条件を、既存のslotとCPU・memory教材の次に学びます。利用者の問いは「容量を増やす前に、容量不足・配置先条件・許容していないtaintを区別できるか」です。taintはnode側の配置制限、tolerationはpod側の許容条件です。

## 固定する環境と順序

2nodeと1podの有限模型です。AはCPU4・memory4、label `pool=general`、taintなし。BはCPU4・memory2、label `pool=special`、taint `reserved=team-a:NoSchedule`。podの要求はCPU2・memory1です。数値は独自の整数単位で、実使用量・millicpu・MiBではありません。入力のavailableは予約配置に使える残量で、実測値ではありません。両nodeは利用可能という仮定を固定します。

各nodeについてCPU、memory、nodeSelector、taintの4条件をすべて評価し、全条件を満たす集合を `feasibleNodes` とします。その集合と、教材固有の選択順A→Bを分離します。複数候補がある時にAを選ぶのは、この教材の決め方です。Kubernetesのscoreや実際の選択順ではありません。

正常版の `selectionCandidates` はfeasible集合そのものです。故障版はtaintだけを無視して候補を作りますが、4条件の表示とfeasible集合は同じです。選択結果がfeasible集合の外なら配置条件違反です。候補が空なら `selectedNode=null`、`outcome=PENDING`。候補があれば先頭を選び `outcome=BOUND`。BOUNDは模型内の選択結果で、Running・Ready・通信成功ではありません。実予約や入力の変更はしません。

## 六つの条件と実装前の手表

| 条件 | selector | toleration | Bのavailable | feasible集合 | 正常版選択 | taint無視の候補／選択 |
|---|---|---|---|---|---|---|
| no-constraint | なし | なし | 4/2 | A | A | A,B／A |
| selector-only | pool=special | なし | 4/2 | 空 | Pending | B／B（違反） |
| toleration-only | なし | team-aと一致 | 4/2 | A,B | A | A,B／A |
| selector-and-toleration | pool=special | team-aと一致 | 4/2 | B | B | B／B |
| wrong-toleration-value | pool=special | team-bで不一致 | 4/2 | 空 | Pending | B／B（違反） |
| capacity-block | pool=special | team-aと一致 | 1/2 | 空 | Pending | 空／Pending |

tolerationだけを足してもA/Bの候補からBを選ぶ保証はありません。selectorを加えると候補がBに限定されますが、容量条件も必要です。正常版は3件BOUND・3件PENDING、故障版は5件BOUND・1件PENDINGで、そのうち2件は配置条件違反です。この件数は固定6条件だけの予測です。

## 入力と拒否の境界

要求は `available`、`nodeSelector`、`tolerations` の3keyだけです。availableはA/Bそれぞれcpuとmemoryを持ち、boolでない整数0〜固定容量を許します。nodeSelectorは空objectか `pool` だけで、値はgeneralまたはspecial。tolerationsは0〜1件、各要素のkeyはkey/operator/value/effectのみ、値は順にreserved/Equal/team-aまたはteam-b/NoScheduleです。省略default、Exists、空key・空effect、別label、複数taintはこの契約へ補正しません。

拒否順は要求schema→available→selector→tolerationです。保存する拒否4例は未知の要求key、availableのbool、未知selector key、operator=Exists。結果は `kind=input-refused`、固定reason、`payload=null` で、配置候補やBOUND/PENDINGを返しません。実Kubernetesがこれらすべてを拒否するという意味ではなく、教材の限定入力範囲です。他のschema端点はコードが拒否しても実測済みに数えません。

## 受入と使える範囲

producer実装前に[固定入力](cases.json)と[手期待](expected.json)を固定し、別担当は独立literal表と集合の積から照合します。6要求×2方式の12応答、全nodeの4判定・feasible集合・候補順・選択・入力不変、4拒否を保存します。独立検査はproducerをimportせず、故障2件を成功配置へ含めません。

画面は保存した模型の計算結果を読むreaderです。予想→保存結果→正常/故障の比較→原典/実装→答え→実務判断の順にし、色だけで判定を示しません。条件・予想・reset・取得失敗・古い応答の際は旧結果・答え・実装を消します。前提2本文・Skill・原典へ戻れる導線を用意します。

Kubernetes・Docker・実podは起動しません。NoExecuteによる退去、PreferNoSchedule、affinity全般、topology spread、複数podの最適化、admission、score、並行更新、Readyと可用性は未対応です。既存容量模型やその独立全列挙を新しい成果として数えません。共有元ownerの現在状態は未確認で、独立pathだけを使います。

現在は契約・手期待の保存段階です。計算とGUIの実施状態は確認記録で別に示し、この文章を過去の契約として保持します。

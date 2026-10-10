# Robotics / autonomous systems — map・経路・衝突・観測を分ける

このrepoから対象分野を学ぶ入口。今回は**2D固定gridの点robot・BFS・閉cell衝突・一回の観測更新**の有限1教材。実ロボット・実センサー・ROS・物理運動・安全保証は未実行。

## 学習の道筋

1. **前提**：整数座標、cell、graph、queue、線分、状態/時刻。mapは知っている世界、worldはtoyの実際の障害物で、同じとは限らない。
2. **主要概念・仕組み**：4近傍/unit costのBFS、経路長、線分と占有cellの接触、map version、観測→停止→再計画。最短性と非衝突は別の検査。
3. **今回実装・正常異常**：[Browser map](index.html)で予想→操作→比較。[robot.py](robot.py)を[独立oracle](verify.py)と読む。迂回経路、直線反例、接触、到達不能、予算、stale mapを比較する。
4. **実務判断**：初期mapで経路が見つかっても、そのまま実行できる根拠にはならない。観測更新後の次のedgeを再検査し、停止/再計画/到達不能を区別する。距離最短が速度・clearance・risk最適とは限らない。
5. **限界**：zero-size点、位置は正確、cellはbinary、4近傍・等cost、停止は瞬時、updateは固定。一回追加だけでnoise・unknown・誤検出・遅延・制動は未実装。実機へ適用した安全保証ではない。
6. **原典→次の学び**：[一次資料locator](sources.json)と[coverage](coverage.json)からfootprint、timestamp/unknown、制動、weighted costの4実験へ進む。

## 予想→操作→比較→原典/実装→答え

予想：startとgoalが自由なら直線は通れるか。BFSが見つけたpathは新しい障害物が出ても有効か。cell角へ触れるだけなら非衝突か。停止後に必ず再計画できるか。

module directoryでPython標準ライブラリのみ。外部API・依存追加不要。

```sh
python3 verify.py
python3 serve.py --port 0
# startupに表示した実際の127.0.0.1 URLを開く。終了はCtrl-C。
python3 route.py collision
python3 route.py real-robot
```

操作：[UI](index.html)でcaseとreplan/stop/ignore-updateを選び、traceを一段ずつ進める。初期BFS pathと直線、現在のknown/world obstacle、robot位置とmap version、停止edgeを比較。UIは記録の再生で、実ロボットやライブsensor映像ではない。

モデル：gridは1..16×1..16、cell中心(x,y)、占有cellは[x−0.5,x+0.5]×[y−0.5,y+0.5]の**閉領域**。境界/角の接触も衝突。点robotをcell中心間で4近傍移動する。naiveはstart→goalのEuclidean線分で、4近傍path/実行可能trajectoryではない。移動予算0..64は成功MOVE回数を数え、観測・検査・再計画は消費しない。探索は各cellを最大一回展開、missionも有限bound。比較する長さは**4近傍edge数**で、実時間/メートル/速度ではない。

|固定case|正常/意図異常/境界|比較結果|
|---|---|---|
|wall-detour|壁にgapあり|BFS10edgeでREACHED、直線はwallへCOLLISION|
|open|障害物なし|BFS6edge、直線CLEAR|
|corner-touch|直線が占有cell角に接触|BFS4edgeでREACHED、直線COLLISION|
|sealed|壁にgapなし|NO_PATH、直線COLLISION|
|same-cell / one-column|同位置/幅1|0edge / 3edgeでREACHED|
|move-budget-one / zero-budget|移動予算不足|1MOVE / 0MOVEでBUDGET_EXHAUSTED|
|stale-obstacle|初期map空、2MOVE後に[3,2]追加|[2,2]で次edgeをSTOP_BEFORE。replanは残り6edge、合計8MOVEでREACHED。stopは2MOVEでSTOPPED。ignoreはmap version0のまま次edgeでCOLLISION|
|stale-sealed|幅5×高さ1、1MOVE後に[2,0]追加|replanはNO_REPLAN、stopはSTOPPED、ignoreはCOLLISION|

比較の注意：ignore-updateのCOLLISIONはtoy worldに対する**命令edgeの接触検出**。contact点を記録し、blocked cellへMOVEしたとは記録しない。物理衝突や実機を壊した実験ではない。観測は著者がafter_movesで指定した固定イベントで、実sensorから推定していない。

原典/実装：[LaValle Planning Algorithms](https://lavalle.pl/planning/) Ch2/§2.3でgraph最短計画、Ch4/5でconfiguration spaceとcollisionを読む。[Nav2環境表現](https://docs.nav2.org/jazzy/getting_started/navigation_concepts/environmental_representation/)でcostmap/footprintを、[Obstacle Layer](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/costmap_2d/costmap_plugins/obstacle/)でobservation_sources/persistence/update rateを読む。今回Nav2/ROSの実行や規格適合はない。[robot.py](robot.py)のBFS、slab clipping、OBSERVATION/CHECK/STOP_BEFORE/REPLANを別々に照合する。

答え：freeな両端だけでは直線の非衝突を保証しない。古いmapの最短pathは新しい障害物で失効する。更新して次edgeを検査したguardは進入前に停止するが、detourがなければ再計画できない。角接触はこのclosed-cell定義で衝突。これらは本教材の点gridに対する判断で、幅・位置誤差・速度を持つ実robotには追加のmodelが必要。

## Subject主要未教材coverage

[具体的な概念/問い/次の実験](coverage.json)と[公式locator](sources.json)を対応させる。

|領域|次に学ぶ概念と問い|今回の状態|
|---|---|---|
|幾何/robot model|座標transform、C-space、footprint/clearance、剛体/関節。幅を持つrobotは通れるか|点cellのみ|
|知覚/sensor|lidar/camera、calibration、occlusion、noise、detection、latency。何からいつ知るか|未教材|
|localization/SLAM|odometry、pose uncertainty、filter、loop closure、alignment。位置がずれたらどうか|未教材|
|map|occupancy/cost/unknown、marking/clearing、timestamp/version、fusion。mapの新しさは揃うか|固定追加のみ|
|global planning|BFS/A*/Dijkstra、reachability、RRT/PRM、optimization。どのcostの最短か|BFSのみ|
|trajectory/control|速度/加速度、nonholonomic、tracking、feedback、MPC、制動。停止できるか|未教材|
|collision/risk/safety|clearance、uncertainty margin、停止距離、failure、emergency stop。geometry以外は何か|閉cellのみ|
|dynamic/task/recovery|moving obstacles、replan、stale観測、mission/cancel。停止後どうするか|一回更新のみ|
|multi-robot/manipulation|space-time、coordination、IK、joint/grasp/contact。2D点で足りるか|未教材|
|middleware/実機/eval|ROS/TF/message、sim-to-real、hardware timing、logs/metrics。追試条件は揃うか|未教材|

次の4実験（未実施）：①固定radiusのfootprint膨張と狭い通路を独立距離oracleで比較（[costmap](https://docs.nav2.org/jazzy/getting_started/navigation_concepts/environmental_representation/)）。②timestamp/versionの遅延・逆転・期限切れ/unknownを保守停止と比較（[observation](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/costmap_2d/costmap_plugins/obstacle/)）。③1D制動距離と観測遅延を手計算して瞬時停止との差を示す（[LaValle Ch13/15](https://lavalle.pl/planning/)）。④weighted gridでDijkstra/BFSと全小graphの独立最小costを比較（[Ch2](https://lavalle.pl/planning/)）。

## 再現証拠・検査

[fixtures](fixtures.json)、[手書きoracle](oracle.json)、[raw](observations/raw.json)、[receipt](observations/receipt.json)。UTC時刻、Python/OS/architecture、input/source/artifact SHA-256を結合。hashは同bytesの識別で、実機安全の証明ではない。rawはmap/world/version・plan/expanded・各MOVE/check/停止・contactを保存。seed20261005の100gridと400geometry入力/結果も保存する。

通常 `python3 verify.py` はread-only、原票更新だけ明示 `python3 verify.py --record`。独立oracleはrobotのBFS/geometry/validatorを使わず、別のlayer-BFSで距離、整数orientation/線分交差で閉cell接触を検査。10case×3policy、手動geometry5件、random400geometry/100grid、不正input14件/option2件、roadmap/local links/source bindingを検査。[限定Skill](skills/atlas-robotics-autonomous-systems/SKILL.md)は既存runner/checker/UIへroute。作者smokeを独立AgentEvalとは呼ばない。

[実IAB QA](observations/ui-qa.json)、[検証記録](VERIFICATION.md)はcapture取得とファイル保存可否、ownedresource終了を区別する。有限1単位で全Subject/Atlas完成は主張しない。

# Atlas — 観測の時刻と更新の時刻

2026-10-07に [Nav2公式repositoryのJazzy branch / observation_buffer.cpp](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_costmap_2d/src/observation_buffer.cpp) を正式webで読みました。狭いlocatorは bufferCloud の cloud.header.stamp と last_updated_、purgeStaleObservations、isCurrent です。branchは読取時点の参照であり、固定releaseへの適合性検証ではありません。

この実装は観測のstampを保持し、更新処理の時刻も別に持っています。保存観測の寿命を調べる処理と、更新が届いているかを調べる処理を分けて読めます。今回の教材はこの違いを考える入口として使い、Nav2自体を実行しません。TTL=4、version順序、同timestamp、unknownによる次edge停止はすべて[本教材の独自規約](CONTRACT.md)です。原典のバッファ削除やcostmap marking/clearingを再実装したとは呼びません。

[Nav2 Obstacle Layer旧URL](https://docs.nav2.org/configuration/packages/costmap-plugins/obstacle.html) は1回の正式取得で404でした。同じ取得を繰り返さず、本文未読として残します。上記の公式source本文とは別の取得結果です。

## 前提への導線

- [点gridの入口](related.html?doc=base)：mapとworld、観測後に次edgeを再検査する。
- [元のcoverage](related.html?doc=coverage)：timestamp-unknownが今回の直接根拠。
- [旧map更新の実装](related.html?doc=base-code)：after_movesで一度追加する方式と、時刻付きの順序検査を分ける。
- [footprint](related.html?doc=footprint)：幅による幾何判定。次2のtimestamp/unknownへ進む。
- [制動距離](related.html?doc=braking)：観測遅延と物理的に止まれる距離は、今回の知識の更新とは別。
- [前提Skill](related.html?doc=prior-skill)：既存の経路・停止・再計画の入口。

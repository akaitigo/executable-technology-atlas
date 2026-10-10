# 点robotが通れる道を、幅のあるrobotも通れる？

[第1単元](../../../subjects/robotics-autonomous-systems/README.md)の点grid/閉cell判定から、既存coverage next footprint-inflationを深掘りする追加単元。固定routeの評価だけで、BFSや新plannerは追加しない。原単元・coverage・rawを保全し、97入口に加算しない。全Subject/Atlas完成を主張しない。

前提: 中心line segment、閉rectangle、半径、最小距離、C-space。仕組み: 円footprintの占有領域Aを移動する代わりに、障害物OをO⊕(-A)へ膨張して中心点routeを判定する。円は対称で−A=A。接触もcollision。[実行前の独立期待](EXPECTATIONS.md)を先に固定した。

| 固定scene | 元obstacleへの最小距離 | radius0 / .25 / .5 / .75 | 判断 |
|---|---|---|---|
| 幅1の通路、中心線y=0 | .5 | CLEAR / CLEAR / COLLISION / COLLISION | r=.5は接触だから拒否、r>.5は重なる |
| 幅2の広い対照 | 1 | 全てCLEAR | このroute/正確なmodelだけの判断 |
| 薄い中間障害物 | 0 | 全てCOLLISION | x=0,1,3,4だけのsamplingは全てCLEARと誤判定 |

[UI](index.html)で **予想→scene/radius/図mode/中心位置を操作→正常/意図異常の比較→原典/実装/raw→答え**。占有円＋元obstacleのworld図と、膨張obstacle＋点中心のC-space図を並べる。中心位置は図を調べるための探針で、拒否routeを実robotで走行した意味ではない。判定は探針sampleではなくsegment全体に対して保存されたもの。意図異常のsample位置も図に表示する。

producerはrectangle膨張を横/縦stripと4corner円の和集合で構成。単なる拡大boxではなくrounded region。独立oracleは元rectangleとaxis-aligned segmentの各軸gapから距離²を求め、r²とFraction厳密比較。r=.5にepsilonを足さず、distance²=r²を拒否。角の手計算対照も検査する。表示用浮動小数/画面pixelが精密判定の根拠ではない。

実務判断: 点中心だけの非衝突やstart/goalのfreeは、footprint付きrouteの非衝突を保証しない。footprintとmapの座標・単位・閉集合接触・clearance規約を合わせ、segment間を検査する。円半径によるdimension marginと、位置推定/センサー誤差/制動距離は別に設計する。Nav2のcost decay inflationをこのbinary幾何判定と同一視しない。

```sh
python3 -B record.py           # current保存原票を読むだけ
python3 -B checker.py          # 独立距離、事前table、raw/binding確認
python3 -B route.py footprint
python3 -B route.py ros        # unsupported exit2
python3 -B preview.py          # own dynamic127.0.0.1、終了Ctrl-C
```

新原票だけ `python3 -B record.py --record` を明示。UTC/UUID名をexclusive作成して旧runを上書きせず、current pointerを更新。入力/source/runtime/command/exit/attemptを結合。数学的COLLISIONはroute拒否であり実行失敗ではない。rawはcompleted evaluations、CLEAR routes、collision refusals、execution failuresを別欄に持つ。初回runの集計keyを明確化したため2回目をcurrentとし、初回rawも保持した。binding更新は `python3 -B checker.py --record-binding` のみ。通常checker/routeはhash/mtimeを変えない。

今回coverage増分: 円footprint、閉集合接触、exact C-space膨張、元obstacle距離oracle、sample間の見逃し。残る次実験3本:

1. **多角形姿勢と位置誤差**: 固定長方形footprintを2姿勢に変え、円近似との過剰拒否/見逃し、誤差marginを区別する。[LaValle Ch4 §4.3](https://lavalle.pl/planning/ch4.pdf)
2. **timestamp/unknown**: 固定観測の期限切れ・順序逆転・unknownで保守停止とnaive更新を比較。[Nav2 Obstacle Layer](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/costmap_2d/costmap_plugins/obstacle/)（次locator、今回本文未確認）
3. **制動と遅延**: 1D速度/減速度・観測遅延から停止距離を手計算し、geometryのCLEARと停止可能性を分ける。[LaValle Ch13](https://lavalle.pl/planning/ch13.pdf)（locatorのみ）

限界: axis-aligned固定中心線、閉rectangle、正確な位置、固定円radius、binary数学geometryだけ。実robot/ROS、polygon姿勢、sensor/pose error、制動、動的障害物、planner、安全保証は未実行。座標単位はmodel単位で、実メートルを測った証拠ではない。screenの実操作は数学教材QA。

[原典](SOURCES.md) · [固定input](fixture.json) · [producer](producer.py) · [独立oracle](oracle.py) · [current](evidence/current.json) · [binding](evidence/binding.json) · [実IAB QA](evidence/ui-qa.json) · [検証](evidence/verification.json) · [限定skill](skills/atlas-footprint-clearance/SKILL.md)

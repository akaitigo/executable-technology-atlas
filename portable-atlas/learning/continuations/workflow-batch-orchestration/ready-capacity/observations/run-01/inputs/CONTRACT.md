# Atlas｜実行できる仕事でも、すぐ始められる？

目標27のDAGと資源容量を扱います。前提は、既存の逐次DAGで学んだ依存・開始・完了と、性能教材で学んだ待ち時間・同時数です。今回は「依存の完了待ち」と「実行可能だがworkerの空き待ち」を分けます。実threadや実workerを起動せず、Python標準ライブラリで有限の仮想時刻を計算します。

## 固定した仕事と時刻

依存は A→B、A→C、B→D、C→D の4辺、仕事はA/B/C/Dだけです。通常の所要時間はA=1、B=4、C=2、D=1 tick。同時完了の対照だけBを2に変えます。tickは秒ではありません。業務値A=2/B=4/C=5/D=9の計算、retryや成功結果の再利用は元教材の範囲であり、ここでは再制作しません。

要求は `capacity`、`durations`、`release` の3項目だけ。capacityはboolでない整数1か2、durationsはA/B/C/Dの4項目で各boolでない整数1..4。releaseは `on-complete` または故障比較用の `on-start` です。固定4条件と入力拒否6例を[cases.json](cases.json)に保存します。拒否順は要求shape→capacity→durations→release。拒否はpayload=null、実行eventなし、入力を変更しません。有限例で全有効入力・全guard端点を網羅しません。

実行区間は半開区間[start,end)。時刻0から始め、次の実完了時刻へ進みます。「実完了」はこの模型で所要時間が経過したことを指し、現実の仕事や業務処理が成功した証拠ではありません。

1. その時刻に終了する**全ての**仕事をID昇順で完了にする。正常版はこの時点で `TopologicalSorter.done()` を呼ぶ。
2. `get_ready()` の返す仕事を待機集合へ入れる。集合はID昇順で扱い、既に取り出した仕事を忘れない。
3. 空き枠があれば、待機集合の最小IDを開始して終了時刻=start+durationを定める。故障版だけ開始直後に `done()` を呼ぶ。
4. **各dispatchの後に再びget_readyを取り込み、空き枠が埋まるか待機集合が空になるまで繰り返す。** 故障版では同じ時刻に下流まで解放され得る。
5. 一連のdispatch後の状態を保存する。未完了があれば、runningの最小終了時刻へ進む。実完了4件まで追い、graphlib側の処理済み件数だけで終了しない。

同時終了を先に全件処理し、その後に開始を行うため、endと次のstartが同じ時刻でも重なりません。readyの順は本教材がID昇順に固定する規則であり、graphlibや一般schedulerの最適性を保証するものではありません。仕事は非preemptiveで、開始後の取消・失敗は扱いません。

## 二種類の待ちと、故障の見方

状態は `dependency-wait`（schedulerが未解放）、`ready-capacity`（get_readyで解放済み・空き待ち）、`running`、`completed` の4種類です。**ready-capacityはschedulerの判断**です。故障版では実際の依存が未完了でも解放されるため、各行へ別に `dependenciesComplete` と `unfinishedParents` を保存します。

`schedulerProcessed` はdoneを通知した集合、`completed` は仮想時刻上で実際に終了した集合です。故障版でこの二つがずれることを隠しません。各仕事の開始時には未完了の親を記録します。全仕事が終了しても、依存に違反した予定を成功したworkflowとは呼びません。

## 先に固定した手予定表

| 条件 | A | B | C | D | 終了時刻 | 依存違反 |
|---|---|---|---|---|---|---|
| 容量1・正常 | [0,1) | [1,5) | [5,7) | [7,8) | 8 | なし |
| 容量2・正常 | [0,1) | [1,5) | [1,3) | [5,6) | 6 | なし |
| 容量2・開始を完了扱い | [0,1) | [0,4) | [1,3) | [3,4) | 4 | A→B、B→D |
| 容量2・B/C同時完了 | [0,1) | [1,3) | [1,3) | [3,4) | 4 | なし |

通常容量1のt=1ではCが空き待ち、Dが依存待ち。通常容量2のt=3では空き1枠があってもDはBの完了待ちです。故障版のt=0ではCが空き待ちと表示されますが、Aは未完了です。固定18時点の状態表も[expected.json](expected.json)へ保存します。これは実装前の予想です。

producerはgraphlibと終了eventを使い、checkerはproducerをimportせず、固定した開始・終了表と整数tickの占有数から照合します。独立レビュー担当も別の期待を先に固定します。容量、辺ごとの依存条件、状態・時刻・集合、拒否payload、入力不変を照合し、欠落・時刻・待ち状態・done集合・拒否payloadの改変を検出します。

## 原典と今回の限界

[Python 3.9 graphlib](https://docs.python.org/3.9/library/graphlib.html#graphlib.TopologicalSorter.get_ready) の `get_ready()` と `done()` を2026-10-06に公式本文で確認しました。完了の通知が後続の解放を決めることが原典との接点です。固定duration、worker容量、ID順dispatch、異常な早期doneは本教材の追加規則です。公開資料3.9.25と既存Mac Python3.9.6の差は記録し、upgradeしません。

予想→保存計算の時刻を操作→正常/故障と二種類の待ちを比較→原典と実装→答え→実務判断の順に学びます。タイムラインと状態図は保存値の説明図で、実workerの計測画像ではありません。

制作時点では計算・GUIとも未実施です。計算は直前の資源確認と実nice10読戻し、短い上限、子1個の有限batch後に記録を分けます。GUIは既存共有ページで確認し、独立受入が終わるまでaccepted:falseを維持します。実並列速度・一般scheduler最適性・公平性・retry/復旧・分散worker・外部副作用・Airflow等の製品適合は未実証です。

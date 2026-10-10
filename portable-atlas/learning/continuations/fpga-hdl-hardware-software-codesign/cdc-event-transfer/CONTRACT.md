# Atlas — 別クロックへ事象を渡すとき、何を見落とすか

## 前提と今回の問い

目標10の「2クロック間のパルス・レベル・トグル転送で失う事象を有限モデルで数える」に対応します。counter教材の旧値からの同時更新、ready/valid教材の捕捉と保持を前提にします。今回は1bitの理想0/1模型です。実RTL、HDL simulation、合成、実FPGAや物理的なCDC安全性の実証ではありません。

## 固定した2クロック

時刻は物理時間ではない整数単位です。sourceの立上りは [0,2,4,6,8,10,12,14,16,18,20,22,24]、destinationは [1,5,9,13,17,21,25]。この入力では同時刻の両edgeを禁止します。初期の送信bit、ff1、ff2、historyはすべて0。reset操作や未知値Xはありません。

sourceのedgeだけで送信bitを変えます。pulse/levelでは事象時刻2に1、release時刻に0とし、それ以外は保持。toggleでは各事象で0/1を反転して以後保持します。levelの解除は別の送信事象として数えません。

destinationのedgeでは、すべてのレジスターを旧状態から同時更新します。

```
new_ff1 = source_bit
new_ff2 = old_ff1
new_history = old_ff2
```

更新後の組合せ出力を pulse/levelでは `new_ff2 AND NOT new_history`、toggleでは `new_ff2 XOR new_history` とします。historyはエッジ検出用で、同期器の2段ff1/ff2とは役割を分けます。この組合せ出力は次のdestination edgeまで値を保ちます。例えばt=9で1になればt=13まで1です。途中のsource edgeで検出数を再加算しません。検出の記録はdestination edge直後の出力1につき1件です。検出数と時刻リストは教学側の観測記録であり、追加の回路レジスターではありません。

## 5つの有限条件

| ID | 方式 | 送信する事象 | 送信bit | 比較すること |
|---|---|---|---|---|
| short-pulse | pulse | t=2の1件 | [2,4)だけ1 | destinationが一度も1をsampleしない |
| held-level | level | t=2の1件 | [2,10)を1に保持 | 何度か1をsampleしても立上り検出は1回 |
| toggle-single | toggle | t=2の1件 | t=2以後1 | 短い事象を状態の変化として保持する |
| toggle-spaced | toggle | t=2,14の2件 | 2で1、14で0 | 両方向の変化を別々に観測できる |
| toggle-close | toggle | t=2,4の2件 | 2で1、4で0 | sample間の偶数回反転は区別できない |

観測はt=25まで。最後の入力事象14の後もdestination edgeを3回含め、2段とhistoryが落ち着く末尾まで保存します。最終の検出時刻の手期待は [] / [9] / [9] / [9,21] / []、検出件数は0/1/1/2/0です。観測終了時の「送った件数−検出件数」は1/0/0/0/2。これは送信事象を知る教学側の数で、宛先が見えない事象数を自力で知るという主張ではありません。

検出できたこの固定例だけで送信時刻と検出時刻を対応付け、差7を遅延とします。未検出の事象は検出時刻も遅延もnull。遅延を0で補いません。宛先の検出器にcase名、送信事象リスト、期待値、教学側の件数を渡しません。入力にある2と14の間隔を一般的な最小許容間隔とは呼びません。

## 検査と入力の境界

[cases.json](cases.json) の5入力と [手時系列](expected.json) を実装前に固定します。各入力は mode/eventTimes/releaseTime の3キー。時刻はboolでない整数で、固定source edgeに限ります。pulse/levelは事象1件と後続release、toggleは事象1〜2件でrelease=null、事象は重複のない昇順とします。不正入力検査はコードに持ちますが、今回の実行対象はこの5例だけです。

source13点・destination7点の和集合20時点で、更新前後の送信bit/ff1/ff2/history、sample、組合せ出力、検出の有無と件数を保存します。期待値との照合は別実装をimportせず行います。さらに、同時更新の破損、検出時刻、保持中の二重計数、toggleの偶数回消失、nullと0の混同、入力型の改変を保存値で有限に拒否します。手表と実装に同じ間違いがないかは別担当の独立表へ照合します。

## 実行と保証しないこと

既存Python標準ライブラリの1子・5秒以内・実nice>=10で1回計算し、資源判定と回収は外側の共通実行器が管理します。作者はtarget/browser/serverを独自に起動しません。この契約と手表は実行前に固定した記録で、現在の実施状態は [確認状態](qa/reader-acceptance.json) から辿ります。

2FFの理想論理が見えることと、metastability（信号が物理的に安定するまでの振る舞い）を測ることは別です。この0/1模型にその物理量はありません。MTBF、setup/hold、clock jitter、resetの安全性、CDC製品macro適合、全速度比、event ID付きexactly-once、handshake/ack、async FIFO、bus転送は保証しません。[原典](SOURCES.md) の製品固有条件を独自模型の保証へ置き換えません。

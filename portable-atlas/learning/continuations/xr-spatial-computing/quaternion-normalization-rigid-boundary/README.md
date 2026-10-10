# quaternion正規化：rigidと可逆を分ける

元[local→world教材](../../../subjects/xr-spatial-computing/README.md)のE1を深掘りする有限unitです。元frame順序・degree/radian→本quaternion/rigid境界→未教材のtracking・pose loss・機器へ進みます。元Source/raw/coverageは凍結。Subject/Atlasはincomplete、入口追加0です。

## 予想→実変換→比較→原典→答え

前提は3D座標、列ベクトル、回転と移動、有理数。既存Python stdlib/Fractionと実Browser DOMMatrixを使い、installなしです。

~~~sh
python3 -B server.py
~~~

動的127.0.0.1 URLを開きます。world点・rigid・inverse往復を予想し、quaternion方針とlocal point x=1/2を選んで「行列生成と実DOMMatrix」。sample literalを表示するだけではなく、Pythonが入力から生成したcolumn-major行列をnew DOMMatrixへ渡し、transformPoint、inverse、inverse.transformPoint、toFloat64Arrayを実行します。RᵀR、det、原点からの距離²、worldとbackを比較し、原典と原票を読んで答えを開きます。所有serverだけCtrl+Cで終了します。

予想3項目とpoint入力変更は新しい値と他の予想を保持し、旧答え本文を空にして閉じます。条件変更は予想unknown/point1へ戻します。実行開始も旧比較をclearし、合成失敗と遅着応答の後に旧答えを表示しません。

## 先に固定した座標・入力契約

[fixtures](fixtures.json)と[hand table](hand-oracle.json)はproducer実行前に固定。右手系、q順xyzw、列ベクトル、world=M×local、M=T×R（回転して移動）、translation=(2,3,0)、point=(x,0,0,w=1)。行列表示はrow別配列、DOMMatrix入力はcolumn-major16値でtranslationはindices12/13/14です。名目単位mの合成値で実空間測定ではありません。

q=(0,0,1,1)はnorm²=2。normalization後はq/√2ですが、unit quaternion公式の二次項(q_iq_j)を元の積/norm²として計算でき、quarter-turn行列をFractionで厳密に作れます。正規化q成分のirrational値をexact rationalと偽りません。scaleしたq=(0,0,2,2)、z−90°=(0,0,−1,1)、identity=(0,0,0,2)も固定比較。任意quaternionや任意軸の実装保証へ広げません。故障版だけnorm²除算を省き、非unit qへunit前提の式を誤適用します。

| q/方針、p=(1,0,0) | world | RᵀR / det | 距離² / 往復 |
| --- | --- | --- | --- |
| (0,0,1,1) 正規化 | (2,4,0) | I / 1 | 1 / 戻る |
| (0,0,2,2) 正規化 | (2,4,0) | I / 1 | 1 / 戻る |
| (0,0,−1,1) 正規化 | (2,2,0) | I / 1 | 1 / 戻る |
| (0,0,0,2) 正規化 | (3,3,0) | I / 1 | 1 / 戻る |
| (0,0,1,1) 故障 | (1,5,0) | diag(5,5,1) / 5 | 5 / 戻る |

故障のR=[[-1,−2,0],[2,−1,0],[0,0,1]]はnonrigidでも可逆です。inverse往復は自身の行列との整合を示すだけで、rigid/期待rotation/所属frameの正しさを示しません。det1だけでも不十分なのでRᵀR=Iも確認。距離保存の数学条件はorthogonalityで、このunitの実距離観測は原点と選択pointの組に限定します。p.x=2では正常距離²4、故障20。zero q、NaN/Infinityを表す明示fixture tokenは行列生成前に拒否し、DOMMatrixも呼びません。これは実APIの例外挙動テストではありません。

Python出力のFractionは厳密一致。Browserはdoubleの絶対誤差≤1e−10という実行前の独自有限教材規約です。WebXRのFloat32精度要件から導出した値ではなく、一般matrix/悪条件の精度保証でもありません。故障inverseのback.y=2.220446049250313e−16を0へ補正せず記録します。

## 再現・独立oracle・記録

~~~sh
python3 -B runner.py --record
python3 -B server.py --record-preview
python3 -B check.py
python3 -B route.py quaternion-normalization-rigid-boundary
python3 -B route.py unsupported
~~~

runner --recordだけ新UTC folderへPython全16条件を保存します。server --record-previewは明示新UTC folderへ実UI由来Browser観測を1実行1fileで保存し、通常serverは記録なしです。--record-previewを終了後、原票を凍結します。checker/routeはread-only、unsupportedはexit2です。

[独立oracle](oracle.py)はproducerをimportせず、先に固定したliteralのquarter-turn/identity/故障行列・world・逆行列を照合します。Fraction積でliteral inverseも確認。DOMMatrixはPython producerの実生成行列を入力に使い、Browser checkerはsource SHA、HTML SHA、UTC/UA、実matrix/inverse/world/origin/back/Gram/det/距離²を固定tableと独立比較します。producer10実変換（rigid8・故障2）、期待入力拒否6。Python6mutantに加え、Browser往復成功をrigid成功へ改ざんするmutantも拒否します。

[検証receipt](observations/verification.json)に実IAB control reset・合成return/HTTP503失敗・実旧応答の遅着破棄・所有preview終了・全file SHA/mtime不変を束縛。合成失敗は実producer障害として数えません。実sandbox bind errno1を保持し、同じowned localhost commandをhost permissionで起動しました。captureはtoolで実表示のみ、保存ファイルなし。同一agentの[module-local Skill](skills/atlas-quaternion-rigid-boundary/SKILL.md) routingを独立Forward Evalとは呼びません。

## 原典と未教材

2026-10-05に[WebXR CRD 2026-06-09 §8.1–8.3](https://www.w3.org/TR/2026/CRD-webxr-20260609/)のcolumn vector/normalization/回転後translationと、[Geometry Interfaces §6.2/6.5](https://www.w3.org/TR/geometry-1/)のcolumn-major constructor、transformPoint、inverse、toFloat64Arrayを確認しました。入力正規化/拒否方針と全例は独自制作、原典本文/図転載なしです。実XRRigidTransformは実行しておらず、仕様適合やWebXR API precisionの実証ではありません。

未教材は任意軸・任意q、SLERP、singular affine、hierarchy、Float32/WebXR API、session・tracking/pose loss・space reset、stereo/comfort、実機・校正・実空間安全、他browser/学習者評価。次案：別fixtureでdet1でもnonorthogonalなshear、singular affineのinverse拒否、qと−q同一rotation、hierarchy所属frameを個別制作する。いずれも未制作。install/権限拡張/課金/公開、Core/fullGate、commit/pushは対象外です。

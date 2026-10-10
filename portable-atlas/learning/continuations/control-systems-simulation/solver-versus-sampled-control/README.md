# solverを替えれば、sampled controllerも安定する？

[第1単元](../../../subjects/control-systems-simulation/README.md)は連続比例feedbackとforward Euler、定常偏差を扱い、40更新の終端時刻がhで変わっていた。この追加単元は[既存LEARNING_PATH](../../../subjects/control-systems-simulation/LEARNING_PATH.md)の実験1を独立fixtureで実行する。本人割当のT=8を固定し、数値solverと入力保持controllerを分ける。既存資料・原票は保全し、入口97へ加算しない。全体網羅0のまま。

前提: 微分/差分、指数関数、feedback、平衡、時刻と刻み幅。仕組み: plant y'=-y+u、比例K2/r1、y0=0、clipなし。連続閉ループはy'=2-3yでy*=2/3。[事前導出](DERIVATION.md)を先に読む。

| 数学model | deviation係数 | 判断対象 |
|---|---|---|
| continuous exact | exp(-3h) | 常時feedbackの基準解 |
| forward Euler | 1-3h | 連続閉ループを数値積分する誤差と安定性 |
| backward Euler | 1/(1+3h) | 同じ連続閉ループのimplicit数値解 |
| sampled hold / plant exact | 3exp(-h)-2 | sample時u=2(1-y)を固定する別controller |

[UI](index.html)で **予想→h/時刻を操作→4model比較→原典/実装/raw→答え**。全てT=8、h=.1/.2/.8/1.6の16条件。グラフは独立縦軸なので見た目の高さを比較せず数値尺度を読む。Eulerの点間線は視覚補間、exact/heldは区間内厳密解のquarter点。終端u(T)は再計算値で次区間は未実行。sampledのu_usedは区間内constant、backwardのu_usedは新stateで評価した数値傾き用で実held-inputと同じではない。

実結果の代表（T=8）:

| h | forward y(T) / a | backward y(T) | held y(T) / a | 判断 |
|---|---|---|---|---|
| .8 | −18.61698 / −1.4 | .66666344 | .65740963 / −.652013 | Euler数値発散だがheldは減衰振動 |
| 1.6 | 528.90112 / −3.8 | .66656510 | 4.17989314 / −1.394310 | backwardの数値安定はheldの安定化を意味しない |

continuous基準はy(8)≈.6666666666415。fixed Tのsolver誤差と、sampledとの**controller model差**を別表示。終端差だけでは過渡の大きさを隠せるため、UIにsample点上の最大差も表示（表示用後処理、全時間supremumではない）。安定判断は|a|と時系列。forward境界h=2/3、held境界h=ln3≈1.098612は事前導出のみで、T/h整数fixture外の境界時系列は未実行。

実務判断: どの微分方程式をsolverで解くかと、controllerをいつ更新し何をholdするかを先に定義する。連続閉ループのbackward Eulerへ替えただけでは、別sampled controllerの周期・gainを変えたことにならない。数値安定と精度も別。実装対象のdelay/clip/noise/締切を含めた検証へ進む。

```sh
python3 -B record.py                # 保存したcurrent原票を閲覧、read-only
python3 -B checker.py               # Decimal80 closed form/初期step/全時系列/binding
python3 -B route.py sampling
python3 -B route.py hil             # unsupported、exit2
python3 -B preview.py               # この単元だけのdynamic 127.0.0.1
```

新原票は `python3 -B record.py --record` を明示。UTC/UUID付き新fileをexclusive作成し、旧runを上書きせずcurrent pointerを更新。source/input/toolchain/attemptとfloat結果・独立Decimal期待値を保存。binding更新のみ `python3 -B checker.py --record-binding`。通常checkerは失敗を原票更新で隠さない。

今回coverage増分: 同じTでsolver比較、sampled-hold厳密plant、異なる2つの安定境界、sample/state/u_usedの規約、独立高精度経路。残る次実験:

1. **PI・飽和・windup**: 固定referenceを高→低へ変え、z蓄積・要求u/clip後u・条件付き積分の回復を比べる。[MIT 6.302 recitation6](https://ocw.mit.edu/courses/6-302-feedback-systems-spring-2007/680f67691cfadcea9aa8a82e6f4c3654_6_302rec6.pdf)（次locatorのみ、今回本文未確認）
2. **delay/noise/量子化**: 1sample遅延と手書きnoise列を個別注入し、true yと測定yを初期手計算で比べる。[SciPy discrete systems](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.dlti.html)（locatorのみ）
3. **solver substepと独立controller周期**: controller周期を固定したままplantの数値substepを変え、held exactへ収束するか比較。今回hは各modelの比較条件で、実機solver設定ではない。[MIT数値法](https://ocw.mit.edu/courses/18-086-mathematical-methods-for-engineers-ii-spring-2006/806b14f6a7a07a2209735c5162b567aa_gv-AB35V2k8.pdf)

限界: 数学CPU simulationだけ。plant/HIL/PID全体、安全、実時間、モデル不確かさ、sensor/actuator、周波数応答/MIMO/同定は未教材・未実証。SciPyや実control hardwareを動かした証拠ではない。利用用server・他task資源には触れない。

[原典](SOURCES.md) · [導出](DERIVATION.md) · [fixture](fixture.json) · [実装](models.py) · [oracle](oracle.py) · [current原票pointer](evidence/current.json) · [binding](evidence/binding.json) · [実IAB QA](evidence/ui-qa.json) · [検証](evidence/verification.json) · [限定skill](skills/atlas-solver-sampling/SKILL.md)

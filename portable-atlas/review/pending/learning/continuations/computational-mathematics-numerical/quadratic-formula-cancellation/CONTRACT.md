# 実装前に固定する有限契約

既知の十進根u,vと十進scale aから、Fractionで厳密にb=-a(u+v), c=auvを作り、各係数を一度floatへ丸める。両方式へ同じfloat係数を渡す。以下の3層を別に表示する。

1. 元の厳密十進多項式の既知根（Fraction、根の順は数値昇順）。
2. float係数を正確な有理数として読み戻した多項式の高精度根。独立oracleはFraction判別式とDecimal sqrt、対称な通常公式を160桁で計算する。240桁で再計算し90桁への丸めが一致することを確認する。fixture最大桁差32桁を事前に見込み、一般の精度保証にはしない。
3. 実Python floatで演算した二つの根。同じ数値昇順で1対1対応し、重根も2個残す。

通常公式はD=b*b-4*a*c、(-b±sqrt(D))/(2*a)。積方式はq=-0.5*(b+copysign(sqrt(D),b))、q/aとc/qを使う。qは絶対値の大きい側を選ぶため正負のbに対応する。a≠1でも分母を2*aとする。FMAや係数再scaleは行わない。

型はint/floatのみ、bool/文字列/非有限値を拒否。a=0、float判別式負、非有限な中間値・根・2*a=0を拒否。q=0はb=c=0の二重zeroだけ[0,0]へ特例化し、それ以外は拒否する。c=0かつb≠0は通常のq/a,c/qでzero根を得る。負判別式をcomplexへ拡張しない。一般係数のsolverではなく、有限fixtureとguardの観測を教材とする。

各根について、元の根への総forward絶対/相対誤差、float係数の高精度根への演算forward絶対/相対誤差、係数変換による根の差を表示する。基準根=0なら相対誤差はnull（未定義）。誤差差分は100桁Decimal、表示は35有効桁、oracleの90桁照合より粗い精度を使う。

代入residualは、計算済みfloat根をFraction.from_floatで厳密化し、元の係数・float係数の両多項式をFractionで評価する。丸めたfloat Horner値をoracleとしない。符号付きp(x)、絶対値、term尺度 |p(x)|/(|a|x²+|b||x|+|c|)、係数尺度 |p(x)|/(|a|+|b|+|c|)を区別する。term分母0ならnull。係数尺度は任意の表示尺度であり、正式なbackward errorや正しい根の保証とは呼ばない。

## 先に置く手表・期待

|fixture|元の根・a|通常/積方式の事前期待|
|---|---|---|
|ordinary|1,2 / 1|両方式1,2|
|fnc-separated|1e-6,1e6 / 1|通常small≈1.00000761449337e-6、積small=実float 1e-6。元の厳密根とfloat 1e-6は等しくない|
|severe|1e-16,1e16 / 1|b_float=-1e16,c_float=1。通常small=0、積small=1e-16|
|scaled-severe|1e-16,1e16 / 1e-12|b_float=-1e4,c_float=1e-12。通常small=0。x=0の絶対residual≈1e-12、係数尺度≈1e-16、term尺度=1で、総相対forward error=1|
|negative|-1e6,-1e-6 / 1|b正、積方式は符号選択が必要|
|mixed|-2,3 / 1|両方式-2,3|
|zero|0,2 / 1|両方式0,2、zeroの相対誤差はnull|
|double-zero|0,0 / 1|q=0特例、両方式0,0|
|near-double|1,1.00000001 / 1|float判別式が0へ相殺し、両方式近い2根を潰しうる。積方式の万能改善を期待しない|
|rounded-double|1,1.0000000000000001 / 1|float係数は1,-2,1。高精度float多項式も重根1、元の第2根との差は変換差|

severeの手計算: D_float=1e32、sqrt(D_float)=1e16、(-b-sqrt(D))/(2a)=0。x=0を元の多項式に入れるとp(0)=1。scaleだけ1e-12へ変えるとp(0)=1e-12となるが、根の総相対誤差は1のまま。

## 原典

[FNC Stability §1.4.1](https://fncbook.com/stability/) Case study・Example 1.4.1を2026-10-05 UTCに確認した。Example 1.4.2の根の積から得る経路も読んだ。教材コードを転載せず、同じ問いを3層oracleとFraction residualで独自に実装する。原典のa=1例の数値を任意aやこのruntimeの全入力へ広げない。

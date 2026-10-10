# 原典と教材独自の規約

[FNC Newton’s method](https://fncbook.com/newton/) の Definition 4.3.1／式4.3.2で、接線から得る更新式を読みました。局所的な収束の説明には関数や根、開始位置の条件があります。本教材の0↔1はその説明を一般の開始値へ広げないための固定対照です。

[SciPy bisect公式文書](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.bisect.html) の Parameters で連続性・端点符号・最大反復を、Notesで停止精度の規約を読みました。本教材の区間幅1/8は独自の規約であり、SciPyのxtolやrtolと同一ではありません。

[SciPy newton公式文書](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.newton.html) の Notes は、更新幅による停止だけでは根の発見を保証しないと説明しています。本教材は残差と更新幅を同時に調べますが、それでも一般の根までの誤差保証を主張しません。実際のSciPyは使用しません。

参照したSciPyページの表示版はv1.18.0。取得先・利用箇所・境界は [sources.json](sources.json) に保存しました。FNCの `/bisection/` は最初の読取りでアクセス不能だったため再試行せず、SciPyの公式本文を使用しました。アクセス不能を記事不存在と判定していません。

5条件、厳密分数、4更新、各しきい値、判定順、端点零、AND条件、履歴schemaはすべて [CONTRACT.md](CONTRACT.md) の独自規約です。原典のコード・製品既定動作・浮動小数の再現実験ではありません。

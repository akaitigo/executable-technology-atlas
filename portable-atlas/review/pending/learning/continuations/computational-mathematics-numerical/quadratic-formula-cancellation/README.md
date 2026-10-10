# 二次公式の桁落ちを3層の根で確かめる

同じfloat係数でも、通常公式と根の積を使う経路で精度が変わる。根1e-16と1e16のfixtureでは通常公式のsmall rootが0、積方式は実floatの1e-16を返す。元の厳密十進根、floatへ丸めた係数の高精度根、実float解を区別し、誤差とresidualを読む教材。

```sh
python3 -B serve.py
```

表示された動的`http://127.0.0.1:<port>`を開く。Python標準libraryだけを使い、依存追加・外部通信・ログインは不要。server停止はCtrl-C。隔離環境ではlocalhost bind/connectが拒否される場合がある。その失敗を記録し、今回の実表示はOS承認された同じ一時serverで確認する。

fixtureと方式を選び、「非zeroの元の根が0になる？」を予測して実行する。「2方式を比較」は同じfloat係数を使う。条件変更で旧結果が消え、resetはsevere/通常公式/未回答へ戻る。原典・契約・実装・検証・Skillは画面の実ファイルsource linkから読める。

## 何を観察するか

1. severeの通常公式で-bとsqrt(D)が同じfloatになる減算を追う。
2. 積方式のq/a,c/qと同じ係数の高精度根を比較する。実floatの1e-16は厳密十進1e-16と等しくない。
3. scaled-severeで、総相対forward error=1でも絶対residualが1e-12、係数尺度が約1e-16になることを確認する。term尺度は1。
4. negativeでqの符号、zeroとdouble-zeroで相対誤差未定義とq=0特例を確認する。
5. near-doubleで両方式が近い2根を潰す例、rounded-doubleで係数変換自体が元の2根を重根に変える例を分ける。

通常公式は数学的に正しい式であり、意図的な欠陥実装ではない。6つの故障変種は正しい分母やq符号、zero特例を実際に変えた別実行で、通常公式と区別する。

## 再現と証拠

```sh
python3 -B verify.py
python3 -B route.py
```

実装前の有限契約・手表は[CONTRACT.md](CONTRACT.md)。[solver.py](solver.py)は実float演算、[oracle.py](oracle.py)はpipelineやfloat solverを呼ばないFraction/Decimal oracle、[lesson.py](lesson.py)は3層比較。係数はFractionで作ってから一度floatへ変換する。元の多項式とfloat係数の多項式のresidualを両方Fractionで厳密評価する。Decimal根は160桁と240桁で90桁丸め一致を確認する。

10fixture×2方式=20比較、13solver入力拒否、6故障変種、全40根について独立Fraction Horner residual照合を行う。初回rawは`observations/attempt-01.json`、core先行証拠・実IAB転記・HTTP・失敗・cleanup・receipt・最後のread-only proofは同directoryにある。[COVERAGE.md](COVERAGE.md)で実測と未確認を区別する。

画面の高精度根は仮数65文字抜粋（指数は保持）、誤差とresidualの表は約6有効桁。raw JSONに160桁oracle、35有効桁誤差、正確な分数、float.hex、係数変換差を保存する。画面の短い数字だけで差を判断しない。

## 範囲と出典

[FNC Stability §1.4.1 / Example 1.4.1](https://fncbook.com/stability/)は式の経路と桁落ちの根拠。根の積の経路はExample 1.4.2も参照した。コード・図を転載していない。原典のa=1例を任意aへ拡張した保証とはしない。

Python 3.9.6、radix=2、mant_dig=53の有限実測。任意係数の誤差保証・全root solver・complex解・underflow回復・FMA・実機性能は未検証。係数尺度residualは正式なbackward errorではない。既存総和・感度教材への増分であり、それらを変更していない。repository全体のCore audit/npm gate、commit、push、公開は未実行。

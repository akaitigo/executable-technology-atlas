# float reductionの加算順序と要素欠落

元のparallel-hpcの整数partitionから、coverage reduction-orderを進める部分教材。次はcomputational-mathematics-numericalで補償和とfloat境界を読む。元Subjectは編集しない。

ID0..3の[1e16,1,-1e16,1]を、既存CPython3.9.6 stdlibで実計算する。sum()は版でalgorithmが変わり得るため、左逐次は0.0から明示addする。隣接pair treeは単一process内で指定順序を再現する。実MPI、実並列到着、性能比較ではない。

|条件|途中値|結果|全入力targetとの差|ID/count|
|---|---|---:|---:|---|
|左逐次|1e16→1e16→0→1|1|-1|0,1,2,3 / 4|
|隣接tree|[1e16,-1e16]→[0]|0|-2|0,1,2,3 / 4|
|math.fsum|内部partialは未公開|2|0|0,1,2,3 / 4|
|ID1欠落|1e16→0→1|1|-1|0,2,3 / 3、違反|
|ID0と2欠落|1→2|2|0|1,3 / 2、違反|

先に予想を選び、Pythonで実行して比較、原典・手表・実装を読み、答えを開く。値が同じ2でもID/count欠落は別問題。誤差0を分割の正しさと読み替えない。

[Python3.9 math.fsum](https://docs.python.org/3.9/library/math.html#math.fsum)は複数partialによる精度改善を説明する。丸め条件やCの拡張精度による二重丸めの制限もある。全入力への正確性や全platform一致は保証しない。

```sh
python3 -B verify.py --record attempt-01  # 未使用attemptのみ
python3 -B verify.py --seal-record       # QA後の明示sealのみ
python3 -B verify.py                     # 実再計算、保存なし
python3 -B route.py                      # 同じ限定route
python3 -B serve.py                      # 動的loopback、終了Ctrl-C
```

手表を実装前に固定。oracleはproducer/集計関数をimportせず、float as_integer_ratioからFractionへ直して全入力exact target2を得る。literal順序別中間値・結果・signed errorとID/countを照合。fsumの内部partialは観測していない。

入力は固定4要素だけ。NaN/Inf/非数値/bool/異なるvector/大指数例を計算前に拒否。overflow/underflowの実挙動、全inputの安定性、異なるPython版、GPU/MPI、速度、利用者理解度は未実証。failureは意図したRuntimeError注入で、基盤の自然故障ではない。

次の実験: 順列別の誤差分布、十進数入力とfloat変換の差、実MPIで到着・reduction順序を記録する（未実行）。共有Portal・元97 Subject・他continuationは読み取り専用。公開、install、commit/push、全repo gateは今回の範囲外。

# Quantum computing: 50/50でも同じ状態ではない

1 qubitのcomplex state vectorと重み付きbranch ensembleを標準Pythonで実行し、coherenceを保つH→Hと、途中でZ基底の測定結果を捨てるH→D→Hを比較する有限教材です。ブラウザで予想、step操作、amplitude／density／Born確率の比較、原典、答えへ進めます。

## 観測と核心

| 経路 | 最終Born P(0), P(1) | 4096 sample counts (0,1) |
| --- | --- | --- |
| H→H | 1, 0（浮動小数点誤差内） | 4096, 0 |
| H→D→H | 1/2, 1/2 | 2045, 2051 |
| H→Z→H | 0, 1 | 0, 4096 |
| H→S→H | 1/2, 1/2 | 2045, 2051 |

seed=20261005。sampleは独立準備・測定を仮定した古典PRNGの有限頻度で、Born確率でも実量子機のshotでもありません。raw浮動小数点値、state、環境、実行時刻は[evidence/run.json](evidence/run.json)。確率50/50はpureな|+⟩にもmixedなI/2にも現れますが、後のHは同じ結果を返しません。

Dはnonselective Z measurementです。結果を条件付けて選別せず、branch weightを保持したensembleにします。mixtureをamplitudeの平均でpure vectorに置換しません。Z/Sはunitaryなphase操作であり、Dとは別です。mixed densityのensemble分解は唯一ではありません。

## 再現する

Repository rootから:

```bash
cd learning/subjects/quantum-computing
python3 -B observe.py
python3 -B verify.py
python3 -m http.server 8797 --bind 127.0.0.1
```

<http://127.0.0.1:8797/> を開きます。終了はCtrl-C。Python 3.9以上のstdlibだけで、install、量子機、Docker、クラウド接続は不要。`index.html`の直接表示も同梱`data.js`を読みます。

`observe.py`は新しいchecker subprocessのstdout/stderrと入力、環境、source version/hashを保存します。UIは保存runのstageを表示するだけで、操作中にPython再実行や再抽選はしません。再観測後はreloadします。

## 実装・原票・原典

- [simulator.py](simulator.py)：state validation、H/Z/S、branch dephasing、密度行列、Born、PRNG。
- [verify.py](verify.py)：branch simulatorと別の2×2行列経路UρU†／D(ρ)=diag(ρ)、既知解析値、H†H、H²、normalization、raw/source/UI binding。invalid input 13件、false evidence 4件を拒否。独立な実装経路ですが、別理論や外部reviewerによる証明ではありません。
- [evidence/stdout.json](evidence/stdout.json)：全stageの生complex値（real/imag pair）、density、sample。
- [evidence/interference.svg](evidence/interference.svg)：実シミュレーション結果の再描画。実画面captureではありません。
- [IBM Quantum Learning / Single systems](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information)：Born rule、H、unitarity、phase。
- [同 / Density matrices](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/introduction)：mixtureを扱う表現。URL/locatorは[sources.json](sources.json)。第三者本文は保存していません。

## 範囲とローカル状態

問いは「同じZ測定確率でもH後が異なるか」、成功条件は実complex simulationと行列oracleの一致、UIでの操作・比較です。実量子機の性能やnoiseを検証したとは扱いません。測定の一般的な良し悪しへ結論を拡張しません。

[COVERAGE.md](COVERAGE.md)に全分野の未教材範囲を明示。[画面QA](evidence/visual-qa.json)、[Skill軽量routing](evidence/skill-routing-check.json)は別記録です。module内Skillのみ、global installなし。教材単位のローカル成果で、Portal／量子分野全体の完成や理解度は更新しません。commit／push／公開なし。

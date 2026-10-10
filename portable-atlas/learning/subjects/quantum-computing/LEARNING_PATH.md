# Quantum computingを学ぶ道筋

この文書は[1 qubitの干渉と混合の既存教材](README.md)から、phase、測定条件、channel、多qubitへ進むための補足です。有限教材の補足であり、量子分野全体の学習完了や量子優位性を示しません。次実験は全て未実行です。

## 1. 前提と仕組み

複素数、共役、ベクトル・行列積、正規化、確率と条件付けを理解します。学ぶ順序は **amplitudeとBorn確率 → unitaryとrelative phase → 干渉 → selective/nonselective測定 → ensembleとdensity → channel → tensor productとentanglement → algorithm・誤り訂正・hardware** です。

amplitudeの絶対値二乗が測定確率で、amplitude自体を確率として足しません。ensembleは重み付きdensityの和であり、vectorの平均を一つのpure stateとして扱いません。global phaseとrelative phase、unitaryなphase変更とcoherenceを失う操作も分けます。

同じZ基底の測定確率だけではstate全体は決まりません。pureとmixed、測定結果を保持した条件付きstateと結果を忘れたstate、modelの確率と有限sample頻度を順に区別します。

## 2. 予想から既存実測へ

[UI](index.html)、[simulator](simulator.py)、[独立行列検査の実装](verify.py)、[環境・binding原票](evidence/run.json)、[全stageのraw](evidence/stdout.json)、[保存画面QA](evidence/visual-qa.json)を読みます。今回はsimulation・checker・UIを再実行していません。

| 経路（初期stateは0） | 保存済み最終Born P(0),P(1) | 4096 PRNG sampleのcounts |
|---|---|---|
| H→H | 1,0（浮動誤差内） | 4096,0 |
| H→D→H | 1/2,1/2 | 2045,2051 |
| H→Z→H | 0,1 | 0,4096 |
| H→S→H | 1/2,1/2 | 2045,2051 |

Hの直後はpure |+⟩でZ確率50/50、coherence magnitude 1/2、purity1です。D後はI/2で同じ50/50でもcoherence0、purity1/2です。最後のHで違いが現れ、「50/50だから同じstate」という予想が外れます。H→S→Hの最終50/50はpureであり、確率が同じだけでD経路と同一にはなりません。

DはnonselectiveなZ測定のmodelです。結果を選別しないbranch ensembleと、独立の2×2 `UρU†` / diagonal化Oracleを照合した記録があります。13無効入力と4偽証拠の拒否は有限contractの検査です。独立の実装経路を別理論や外部reviewの証明とはしません。

CPython 3.9.6、1 qubit、H/Z/S、完全dephasing、gate誤差なしの古典simulationです。seed=20261005のPRNGは毎回同じstateを独立準備する仮定で、同じqubitを連続測定した記録でも実機shotでもありません。同確率・同seedの2条件でcountsが一致してもstate一致の証拠にはなりません。UIは保存stageの再生、interference.svgは結果の再描画です。

## 3. 実務で何を判断するか

検証したいobservable、準備、basis、gate順序、測定結果の保持、noise、shotsを先に固定します。amplitude、density、Born確率、sampleを別に追い、stateの一致を一つのbasisの頻度だけで判断しません。

実hardwareへ進むならdevice、calibration、gate/readout誤差、mapping/transpilation、実行時刻、統計的不確かさを記録します。小さな理想モデルの一致から量子優位性、algorithmのscale、誤り訂正や実機の性能を結論しません。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [IBM Quantum Learning, Single systems / Quantum information](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information)、Measuring quantum states / Unitary operations / Compositions of qubit unitary operations | Born、H、phase、gate合成 |
| [IBM Density matrices / Introduction](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/introduction) | mixtureと部分systemを扱う表現への入口 |
| [IBM Multiple systems / Quantum information](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information)、Tensor products / Bell states / Partial measurements、CNOTの記述 | tensor順、entanglement、条件付き測定、多qubit gate |

既存bindingは[sources.json](sources.json)にあります。次の連続phase・部分dephasingは定義を明記した独自拡張案で、既存H/Z/S/D実装の実行済み範囲ではありません。

## 5. 未教材と次の問い

| 未教材 | 問いと次の入口 |
|---|---|
| 連続relative phase・global phase | Bornが同じでも後のHで何が変わるか。実験1 |
| selective測定・記録・条件付きstate | 結果を知るbranchと忘れたensembleはどう違うか。実験2 |
| 部分dephasing・channel | coherenceを有限の強さで減らすと干渉はどう変わるか。実験3 |
| tensor・CNOT・Bell・reduced density | 同じ局所stateでも全体の相関はどう違うか。実験4 |
| POVM・tomography・open-system dynamics | 複数basisと一般channelをどう扱うか。別教材が必要 |
| Grover/Shor/QFT・variational・compiler・complexity | algorithmの資源と成功条件は何か。未実装 |
| 通信・暗号・error correction/fault tolerance | 情報・誤り・信頼の仮定は何か。未検証 |
| hardware/calibration/readout・cloud・量子優位性 | 理想modelとの差とscaleをどう測るか。実機実行なし |

既存[COVERAGE.md](COVERAGE.md)の未教材状態を保持します。

## 6. 次の実験案（4本、全て未実行）

1. **relative phaseとglobal phaseを別に比較する。** 独立fixtureで `Pφ=diag(1,exp(iφ))`、φ=0,π/2,πを定め、H→Pφ→HのBornを手計算 `(1±cosφ)/2` と独立行列積へ照合します。別条件でvector全体に同じphaseを掛け、densityと全測定確率の不変を確認します。予想は中間Z確率が同じでもrelative phaseで最終確率が変わることです。Single systemsが入口で、任意gate全体や実phase noiseは未実証です。

2. **測定結果の保持と破棄を比較する。** 独立fixtureの|+⟩にZ射影を適用し、結果0/1それぞれの確率・正規化された条件付きstate、その後Hの結果を保存します。両結果を重み付きで合計したdensityと、結果を忘れるDを別経路で照合します。予想はbranchごとのpure stateと平均したmixed stateが違うことです。手書きprojectorとBorn表をOracleにし、確率0のbranchを無理に正規化しません。原典はMeasuring quantum statesとdensityの導入です。一般POVMや実測定recordは未実装です。

3. **独自の部分dephasingを有限値で比較する。** `E_p(ρ)=(1−p)ρ+pD(ρ)`、p=0,1/2,1という凸結合を定義し、H→E_p→Hを比較します。独立density経路と重み付きbranch経路を、手書きのcoherence `(1−p)/2`、最終P(0)=1−p/2、trace・positivityへ照合します。予想は干渉が連続的に弱まることです。densityは概念入口ですが、このpを実deviceのdephasing率やT2と同一視しません。連続時間noise・channel全体の証明は別条件です。

4. **Bell stateと古典相関mixtureを比較する。** 別の2 qubit fixtureでbasis順00,01,10,11、先頭qubitをcontrolと定め、|00⟩へH⊗IとCNOTを適用します。Bellのdensityと、00/11各1/2のmixtureを手書き4×4行列・独立tensor計算へ照合します。予想はZの同時確率と各局所I/2が同じでも、両qubitへHを掛けるX基底比較でjoint確率が違うことです。Multiple systemsのBell/partial measurement/controlled操作が入口です。相関だけをentanglementの一般判定にせず、Bell不等式・実機・多qubit scalabilityは未実証です。

## 7. 資料取得と検証状況

2026-10-05に上記IBM 3ページのHTML本文を取得して参照箇所を確認しました。今回本文取得不能のURLはありません。第三者本文・notebook・実deviceデータ・Credentialは保存していません。

追加はこの文書だけです。simulation、checker、server、UI、量子機、global gateを実行せず、旧原票・QA・digestを更新していません。次実験の解析的予想は新しいsimulationや実機の証拠ではありません。

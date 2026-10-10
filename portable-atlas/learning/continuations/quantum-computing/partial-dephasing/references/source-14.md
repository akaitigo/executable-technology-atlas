# 観測範囲と未教材

今回実行したのは古典計算機上の1 qubit数学モデルです。

- complex pure vectorと正規化されたbranch ensemble、density matrix、Born確率。
- H→H、H→D→H、H→Z→H、H→S→Hの全stage。
- unitary norm保存、H†H=I、H²=I、density trace／Hermitian／positivity／purity。
- 4096独立shot相当のseed固定PRNG sampling。exact model probabilityとは別。
- 無効normalization、未対応gate、多qubit入力、NaN、bool、shots/seed、branch weightの拒否。
- 保存raw/source/UI binding、独立2×2 oracle、false evidence negative。

## 仮定

initial |0⟩、1 qubit、H/Z/Sだけ、Z基底完全dephasing、gate誤差なし、有限double精度。Dは結果を忘れるmeasurement channelのモデルで、個別measurement recordの条件付きtrajectoryは実装していません。最終sampleは毎回同じ準備をした独立測定を仮定し、同じqubitを繰り返し測っているわけではありません。

混合stateは単一amplitude vectorでは表せません。phase矢印はpure branchの説明で、ensemble全体の唯一なphaseではありません。global phaseは観測できず、relative phaseを比較します。

## Quantum computing分野の未教材Coverage

Bell／entanglement、tensor product、多qubit gate/CNOT、量子回路compiler、Shor/Grover/QFT、variational algorithms、量子通信、量子暗号、error correction/fault tolerance、hardware/calibration/readout、実noise model、open-system dynamics、POVM、tomography、検出効率、実量子機／クラウド、量子優位性とcomplexity theoryは今回未実装・未実行です。任意inputや全gate／全channelの正当性証明ではありません。分野全体の知識網羅、学習者理解度も未評価です。

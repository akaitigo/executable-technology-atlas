# 有限契約と実装前手表

入力はrho（2×2 complex density、成分pair[real,imag]の各値は有理数文字列）とrecord（整数0/1または"discard"）。成分は整数/p/q文字列、分子絶対値100以下・分母1..1000。JSON数値は成分に使わない。rhoはHermitian、trace1、diag非負、det>=0をexact検査。余分なキー、bool、非finite/float、不正shape、ゼロ分母、不正densityを拒否。recordの0/1は説明のための条件付きbranch指定で、実shotの記録ではない。

1qubit Z射影P0=diag(1,0),P1=diag(0,1)。σk=PkρPk、pk=Trσkを別fieldで保存。pk>0だけρk=σk/pk、traceρk=1。pk=0はbranch UNREACHABLE、conditional/conditional_trace/H後conditional/H後Born=null、σk=0。測定全体は正当なまま。pk=0を無理に割らず、別faultだけでZeroDivisionErrorを実行して捕捉する。

記録破棄のweighted densityはΣpkρk（到達不能項は寄与0）。別経路の直接diagonal map diag(ρ00,ρ11)と全行列を照合。HはR=[[1,1],[1,−1]]を用いRρR/2でexact計算し、√2をfloat近似しない。H後もweighted branch sum、H(weighted)、H(direct)の全densityを照合する。各conditional branch H後のZ Bornは[1/2,1/2]。ensembleも同じZ Bornだがdensityの非対角は重みに依存する。

|入力|p0,p1|branch0/1の正規化trace|記録破棄density|H後densityの非対角01|正規化漏れのensemble trace|
|---|---|---|---|---|---|
|∣+⟩ (density成分1/2)|1/2,1/2|1,1|diag(1/2,1/2)|0|1/2|
|3/5∣0⟩+4/5∣1⟩|9/25,16/25|1,1|diag(9/25,16/25)|−7/50|337/625|
|∣0⟩|1,0|1,null|diag(1,0)|1/2|1|
|∣1⟩|0,1|null,1|diag(0,1)|−1/2|1|
|3/5∣0⟩+i4/5∣1⟩|9/25,16/25|1,1|diag(9/25,16/25)|−7/50|337/625|
|diag(3/4,1/4)|3/4,1/4|1,1|同左|1/4|5/8|

biasedのρ=[[9/25,12/25],[12/25,16/25]]。σ0=diag(9/25,0)、σ1=diag(0,16/25)、ρ0=diag(1,0)、ρ1=diag(0,1)。Hρ0H=1/2[[1,1],[1,1]]、Hρ1H=1/2[[1,−1],[−1,1]]。重みを掛けたH後は[[1/2,−7/50],[−7/50,1/2]]。

fault omit_normalizationはσをconditionalと誤認し、さらにpkを掛けてdiag(p0²,p1²)、trace p0²+p1²。equal_weightsは到達可能branchだけを等重み1/nにする（0branchは含めない）。biasedならH後I/2となり正しい非対角−7/50を失う。しかし両者H後のZ確率は[1/2,1/2]で、確率だけの検査は故障を見逃す。zero_divisionはσ/pを全branchに強行してpk0時だけEXECUTION_FAILED、それを正しい測定全体の不正と扱わない。p0=p1や確定stateでは一部故障が目立たない条件も残す。

producerは汎用complex pair行列積でprojector/H、oracleは2×2成分閉式と独立直和/weighted係数。手literalのp、H後非対角、fault trace、selection状態も照合。PRNGなしexact densityの理想CPUモデル。実機shot/実測定record、一般POVM、多qubit/Bell、量子優位性はUNOBSERVED。

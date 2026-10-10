# 有限契約・実装前手表

受信入力はknown_pilot/pilot_rx/payload_rx各4個のI,Q有理数pairとmin_gain_sq/max_residualのみ。正解payload bitsは入力に含めない。成分は整数またはp/q文字列、分子絶対値100以下・分母1..1000、座標絶対値4以下。閾値は0..4。bool/float/余分なキー/不正shape/ゼロ分母は拒否。合成4symbolの1sample/symbol、実sample clockでない。

複素gain ĥ=Σconj(p)r/Σ|p|²、known energy Ek=Σ|p|²。h2=|ĥ|²（magnitudeの二乗、sqrtを取らない）。fit=ĥp、SSE=Σ|r−fit|²、normalized residual NR=SSE/Er、Er=Σ|r|²。分母は受信pilot energyでありpayload energyでもEkでもない。

gateはh2>=min_gain_sqかつNR<=max_residual。等値は採用。default min=1/4、max=1/2の独自教材gate。先にEk=0ならNO_PILOT_ENERGY、h2=0ならZERO_GAIN（Er0時NR=null）。naiveもゼロは逆数を作らず拒否するが非0の品質gateを無視する。gatedはLOW_MAGNITUDE/HIGH_RESIDUALの両方を記録できる。

採用だけpayload/ĥを複素除算、実部<0ならbit1、実部>=0（tie含む）ならbit0。拒否はcorrected/decisions=null、demodulated=false。独立harnessだけが真の4bits[0,1,0,1]と照合する。拒否はerror_count/BER=null、compared_bits=0、verdict=REFUSED。期待拒否を成功受信に数えない。acceptedでもerror_count>0ならACCEPTED_ERROR。BER分母は実際に比較した4payload bitsのみ、確率BERではない。

|case|ĥ|h2|Er/SSE/NR|gated判定|gated/naive誤り数|
|---|---|---|---|---|---|
|clean-real|1|1|4/0/0|採用|0/0|
|clean-j|j|1|4/0/0|採用|0/0|
|magnitude-equal|1/2|1/4|1/0/0|採用|0/0|
|magnitude-below|2/5|4/25|16/25、0、0|低magnitude|未比較/0|
|near-zero|1/20|1/400|1/100、0、0|低magnitude|未比較/2|
|residual-below|1|1|5/1/1/5|採用|0/0|
|residual-equal|1|1|8/4/1/2|採用|0/0|
|residual-above|1|1|20/16/4/5|高residual|未比較/0|
|both-fail|1/4|1/16|5/4、1、4/5|両方拒否|未比較/0|
|zero-gain|0|0|4/4/1|推定不能|未比較/未比較|
|zero-rx-energy|0|0|0/0/null|推定不能|未比較/未比較|
|zero-known-energy|null|null|4/null/null|推定不能|未比較/未比較|
|inverse-pilot-consistent|−1|1|4/0/0|採用|4/4|
|payload-error|1|1|4/0/0|採用|1/1|
|decision-tie|1|1|4/0/0|採用|2/2|

既知pilot p=[1,−1,1,−1]。orthogonal u=[1,1,−1,−1]はΣp u=0。r=p+a uならĥ=1、SSE=4a²、Er=4+4a²、NR=a²/(1+a²)。a=1/2,1,2が上のresidual3条件。r全体を1/2倍するとh2は1/4倍、NRは同じ。residual noiseだけ増すとĥは同じままNRが変わる。UIのscale/noise構築はこのr操作をFractionで行い、構築後のrだけをreceiverへ渡す。

逆位相pilot r=−pはĥ=−1/NR0で採用され、正位相payload[1,−1,1,−1]を全反転する。pilotに整合することはpayload位相の正しさを保証しない。receiver oracleは複素除算を共有せず、成分normal equationsとdot/cross成分で算術を検査する。literalにはĥ/energy/SSE/NR/拒否/誤り数を手固定する。

MIT Ch8 §8.1–8.2は検出・確率model・MAPの原典入口。本閾値はMIT所定gateでもMAPでもない。実RF、規格、機器性能、確率BER一般、timing/ISI/周波数driftはUNOBSERVED。

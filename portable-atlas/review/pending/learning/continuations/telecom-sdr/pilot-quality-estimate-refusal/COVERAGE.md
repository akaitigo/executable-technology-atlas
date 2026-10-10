# 有限coverage

|問い|算術・操作・判断|
|---|---|
|magnitudeの境界|below/equal/above、近0とmin0/等値1/400、h2と閾値を別表示|
|residualの境界|below/equal/above、SSE/受信energy分母、両gate独立|
|独立操作|pilot scaleと直交noiseを別操作、閾値2項も別操作|
|推定不能|known energy0/received energy0/gain0、逆数を作らず拒否|
|品質拒否|LOW_MAGNITUDE/HIGH_RESIDUAL/両方、復調なしBERnull/0bit|
|採用して誤る|整合逆位相pilot4/4、payload固定noise1/4、tie2/4|
|receiver/harness分離|receiver stdinにtruthなし、harnessだけ誤り/BER/成功受信数|
|実UI失効|全編集、条件reset、保留古い応答、実503、producer故障|

固定18+任意4条件、さらに独立scale/noise操作を実UIで検査する。producerは複素pair演算と残差加算、oracleは成分normal equationsとSSE=Er−h2 Ek。手literalは実装前固定。raw/receiptとI/Q図dataset、全pilot算術表、復調表、答えを照合する。

実RF/SDR/GNU Radio/機器、規格、波形stream、実clock、MAP/ML、確率BER一般、タイミング/ISI/周波数driftはUNOBSERVED。期待拒否は合格検査だが成功受信ではない。Skillはこの単位だけで利用する。

# 有限coverage

|問い|算術とUI・判断|
|---|---|
|σとconditionalの差|projector積/trace pk/除算後trace1を別field|
|確率0のbranch|basis0/1の到達不能、conditional/H後null、測定全体はOBSERVED|
|不均等重み|biased p9/25・16/25、H後非対角−7/50|
|記録保持と破棄|record0/1/discard、conditional/weightedを別表示|
|H後のfull density|weighted-after-H / H(weighted) / H(direct)を全成分照合|
|等重み故障|H後確率は同じでもfull density違い、半々と確定stateではlatent|
|正規化漏れ/zero割り|p² weighting/trace337/625、別faultだけZeroDivisionError|
|入力とUI失効|density/schema拒否、record/予想/JSON/条件/reset、旧保留/503|

固定13（実行故障1含む）+任意4。位相付きpure density、mixed、稀なbranchも含む。producerは汎用pair行列積、oracleは2×2閉式とweighted係数、手literalは実装前固定。図・全表・答え・raw/別receiptを実UIで照合する。

一般POVM、実機shot/測定record、PRNG、2qubit/Bell、多qubit、量子優位性はUNOBSERVED。説明上のbranch指定を観測記録と呼ばない。既存nonselective DとBell教材は変更せず、この単位のnormalization/weight/recordを追加する。

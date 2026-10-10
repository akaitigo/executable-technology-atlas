# Atlas：実装前の手計算

Token id は initializer 呼出し番号です。生成の順番ではありません。ここは測定結果ではなく、固定本文から追った予測です。

|問い|順序|値が返るか・初期化済みか|
|---|---|---|
|例外・各mode|初期→call1が専用例外→call2がToken2→再読|なし/false→例外/false→2/true→同じ2/true|
|再入・SYNC/NONE|outer call1固定→inner call2生成/返却→outer Token1生成/返却→後の読取り|inner getter=2、outer initializer=1、outer getter=1、later=1|
|再入・PUBLICATION|同じfixtureの順序|inner getter=2、outer initializer=1、outer getter=2、later=2|

内側の生成は先、外側の生成は後です。内側から戻った時点で `isInitialized()` がtrueでも、外側getterが返す値をそこから一律には決められません。外側が作った候補、getterが返った参照、最後の再読取りを別々に比較します。深さ3への到達は今回の正常な期待に含めず、専用guardで停止する実験失敗です。

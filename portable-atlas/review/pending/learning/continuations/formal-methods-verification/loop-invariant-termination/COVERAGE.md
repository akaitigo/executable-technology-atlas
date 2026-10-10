# 範囲と判定

exact JSON整数 n,budget=0..8、normal/double-y。bool、float、範囲外、未知body、追加／欠落keyは拒否。全9×9×2=162入力で途中と境界の全状態を閉式と照合する。

初期状態と本体末尾だけを不変条件の検査点とする。途中の等式値も表示するが保存義務と混同しない。誤本体n=0は空実行なので境界違反を観測しない。n>0,budget=0も初期状態しか観測しない。

終了状態と分類は別フィールド。違反が観測された短budgetでもcompletionはbudget_exhausted、postconditionはnull。n=0,budget=0はguard_exit。通常本体の短budgetは未観測の事後条件をfalseとはしない。

有限観測、閉式照合、紙上の任意自然数の導出を区別する。機械証明、任意プログラムの停止判定、整数overflow、並行実行、mutex graph、旧教材の再実行は範囲外。

実際のUI検証結果と画像・RAMreceiptはqaに保存する。artifact-indexは最後に全候補ファイルのSHAを結び、verificationはmanifestも含めた内容を結ぶ。受理reviewと全体gateは中央担当。

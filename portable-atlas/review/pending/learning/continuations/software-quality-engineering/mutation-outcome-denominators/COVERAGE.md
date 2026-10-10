# 対象と未教材

合成reportの8状態、canonical/故障集計、detected・undetected・covered・valid・invalid・total、3つのratio、0分母undefined、ID/status拒否を扱います。固定20例と18拒否は受理可能な全組合せの証明ではありません。

未教材: 自動変異生成、Stryker runner/CLI、実process timeout、終了上限と生exit/error、完全schema import、testごとのkilledBy/coveredBy、同値性証明、巨大report、途中report更新/履歴、実製品の品質・CI・安全性、全ブラウザ/アクセシビリティ検査。

Timeoutラベルの入力を実timeoutと呼びません。Pending/ignored/invalidをSurvivedへ混ぜた故障の結果を正しい測定として採用しません。元statusと正しい集計を保持します。scoreだけでsurvivorの原因は決まりません。一般的なmutation testingやSoftware Quality/Core全体の完成は主張しません。

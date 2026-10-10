---
name: pi-saturation-windup
description: 独自有限PIモデルの飽和・windupを、旧state更新・区間厳密plant・独立Decimal漸化式・sample窓内整定で学ぶ。
---

# PI飽和とwindupの有限実験

教材は ../..。README/CONTRACT/hand-oracleを先に読み、予想→h/方式/Ki→3方式とP対照→原典/実装/原票→答えの順で実行する。旧y/zから要求uと次stateを求める。条件変更で旧答えを使わない。上限外向き/下限外向き/等値/内向き/e0の規則、Ki0の積分寄与0を照合する。

再現は教材ディレクトリでpython3 -B verify.py。既存原票を上書きしない。install、実plant設定、公開、旧教材修正は含まない。sample帯内初回到達を整定と呼ばない。窓内未整定nullを0へ変えない。plant区間厳密解・離散controller周期・float丸めを区別する。MIT原典は積分概念の入口で、独自anti-windupの承認や安全証明ではない。COVERAGEの未対応を今回の観測で埋めない。

---
name: observation-delay-braking-distance
description: 理想1D点の観測遅延と制動距離を、単位付き手表・独立速度面積・解析接触eventで学ぶ有限simulation。
---

# 観測遅延と制動距離

教材は ../..。README/CONTRACT/hand-oracleを先に読み、予想→fixture/仮定/h→遅延あり/遅延0/瞬時停止→実装/原票→答えの順。接触等値は接触、v0/tau0/T0と初期接触を区別する。停止後負速度を作らない。sample間接触は解析eventで読み、未来event・既知停止距離を窓内停止と呼ばない。

再現は教材ディレクトリでpython3 -B verify.py。既存原票を上書きしない。install、実robot設定、安全距離助言、公開、旧教材修正は含まない。hは表示点間隔で、物理制御周期/solver刻みではない。LaValleは動力学の概念入口であり、独自delay/constant-brake modelの安全承認ではない。COVERAGEの未対応を今回の結果で埋めない。

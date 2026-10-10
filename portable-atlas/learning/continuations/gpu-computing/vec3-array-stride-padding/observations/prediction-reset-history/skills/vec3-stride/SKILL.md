---
name: vec3-stride
description: 固定vec3配列のstrideとpaddingを既存Browser WebGPUで比較し保存原票を照合する限定route。
---

このmoduleだけで `python3 -B verify.py` / `python3 -B route.py` を読み取り専用実行。GPU再実行とは呼ばない。UI再実行は自分の `python3 -B serve.py` のloopbackでadapter probe→小compute/readback、所有資源を終了する。予想→32byte配置→実readback/validation→原典→答えを案内する。stride12/16、last6/8、pad99/-1のみ。GPU不可/validation/driver失敗を隠さずCPU成功で代用しない。既存原票の上書き、依存install、設定変更、課金、公開、commit、Core gateを行わない。native GPU/速度/安全一般は主張しない。

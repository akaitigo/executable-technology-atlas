---
name: atlas-quality-acceptance
description: この架空有限データ教材で正しさAND期限、閾値変更、Paretoと受入の違いを比較する。実利用者の要求決定や実性能測定には使わない。
---

rootは2階層上。`python3 -B route.py acceptance`→README、`compare`→手表、`sources`→NASA locator、`verify`→checker。固定3sampleの欠測/nullはUNKNOWN、完全候補のみParetoへ入れる。正しさと期限をweighted score/ORで相殺せず、非支配を受入や承認と呼ばない。合成data評価は実製品test/再計測ではなくapproval/validation UNCONFIRMEDを保持する。通常はread-only、明示recordだけ新原票。未知routeはunsupported。

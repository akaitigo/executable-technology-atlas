---
name: atlas-revision-proof
description: この有限metadata教材で要求/link/test revision baselineと旧PASS証拠の別失効を比較する。実test再実行や変更承認には使わない。
---

rootは2階層上。`python3 -B route.py baseline`→README、`compare`→手表、`sources`→原典、`verify`→checker。graphはR/Dとlinks、proofはancestor部分graph＋test実装revision/hash。missing linkはUNKNOWN_TRACEを優先し影響なしと解釈しない。new計算を実test再実行・承認と呼ばず、UNCONFIRMED/falseを保持する。通常はread-only、明示recordのみ新原票。旧教材とSubject全体へ完成を拡張しない。未対応routeはunsupported。

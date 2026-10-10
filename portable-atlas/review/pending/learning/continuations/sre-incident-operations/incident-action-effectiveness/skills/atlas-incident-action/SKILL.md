---
name: atlas-incident-action
description: 架空incidentのaction完了と現在buildの再現/regression有効性を実Pythonで比較する有限教材。実本番incidentやCAPA監査には使わない。
---

rootは2階層上。`python3 -B route.py action`→README、`compare`→手oracle、`sources`→Google SRE、`verify`→checker。done-only/別buildPASS/REPROだけPASSを完全有効性と呼ばない。current source/version束縛＋完全7testの実PASSをVERIFIED_FINITEとし、本番有効性/人の承認UNCONFIRMEDを保持する。通常はread-only/memory-only、明示recordだけ新原票。未知routeはunsupported。

---
name: atlas-telemetry-budget
description: 独立合成台帳の既知分母とcollector未知からSLI・予算・burn範囲を比較する有限教材。実pipeline保証や本番pager判定には使わない。
---

rootは2階層上。`python3 -B route.py bounds`→README、`compare`→手Fraction、`sources`→Google SRE、`verify`→checker。seen-only率を全台帳へ外挿せず、未知をgood/badへ埋めない。arrived<=cutoff、N0はNO_ELIGIBLE、target100% burnはZERO_BUDGET/null。negative残予算と未確認の台帳完備/本番保証を保持する。通常read-only/memory-only、明示recordだけ新原票。未知routeはunsupported。

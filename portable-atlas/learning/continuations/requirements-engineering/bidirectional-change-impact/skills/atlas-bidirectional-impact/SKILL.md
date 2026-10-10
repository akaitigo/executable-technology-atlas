---
name: atlas-bidirectional-impact
description: 固定6nodeの要求・設計・testで変更影響と逆trace欠落を比較する有限教材の案内。一般graph解析や要求承認には使わない。
---

まず教材READMEとEXPECTATIONSを読み、起点を含む到達集合と独立保存したforward/reverseを確認する。

- impact: `python3 -B route.py impact` → runner.py。通常実行はread-only。
- verify: checker.pyで保存原票・独立表・行列閉包を照合。
- compare: index.html。2予想→実Python→正常/trace不完全/拒否/失敗。
- sources: NASA SWE-052 §3.4–3.5 locator。

条件resetと各予想欄単独変更を別々に検査する。後者は新予想/他欄を保持し旧raw・比較・答えを消す。INPUT_REFUSEDでも予想比較を維持。EXECUTION_FAILUREは正常答えを隠す。

明示依頼で更新するときだけrunner.py --recordで新receiptを保存し、旧rawを保持する。source変更は新観測が必要。通常checkerはhash/mtimeを変更しない。承認、製品graph、一般影響、安全性、実test結果はunsupported。

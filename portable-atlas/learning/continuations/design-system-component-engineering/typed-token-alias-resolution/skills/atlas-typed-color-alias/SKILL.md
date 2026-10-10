---
name: atlas-typed-color-alias
description: 5固定tokenの型付きcolor aliasからCSSへ変換し、実Browser computedと固定oracleを比較する有限教材の案内。
---

READMEとEXPECTATIONSを読む。元Subjectのtheme/instance所有からprimitive/semantic aliasへ進む。

- tokens: `python3 -B route.py tokens` → runner.py。通常はread-only。
- verify: checker.pyで保存raw・固定参照先/sRGB/CSS・実computedを照合。
- compare: index.htmlで2予想→正常/故障/拒否/実Error。
- sources: DTCG 2025.10 Format/ColorとCSS invalid variables locator。

各予想controlを成功比較→答えdetailsを開く→その予想だけ変更で検査する。新値と他欄を保持、旧答え本文を空にしてdetailsを閉じる。条件resetは両予想を消す。拒否は予想比較を保持。失敗は正常答えなし。

source変更時は新実行、明示recordだけ新UUID rawと実child attempt/exitを保存。旧rawは保持。full-dtcg/brand/package/accessibility/performanceはunsupported。global installしない。

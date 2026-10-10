---
name: atlas-capture-substitution
description: 独自open-term ASTの捕獲回避置換とnaive captureを、手書きfree集合・環境評価で比較する有限教材の案内。
---

READMEとEXPECTATIONSを先に読む。元Subjectのclosure環境を前提にする。

- substitution: `python3 -B route.py substitution` → runner.py。正常exit0、拒否exit2、失敗exit1。
- verify: checker.pyで保存raw・手書きAST/free集合・別環境oracleを検査。
- compare: index.htmlで2予想→正常/naive/拒否/実Errorを比較。
- sources: Stlc Substitutionのclosed-term前提と独自open拡張を確認。

予想欄の単独変更は新値/他欄を保持し旧raw・比較・答えを消す。条件resetは両予想を消す。成功後の拒否/失敗に旧答えを残さない。遅い旧応答はlatest結果を上書きしない。

通常コマンドは証拠更新なし。明示recordで新UUID rawと実child attempt/exitを保存、旧raw保持。source変更は新実行が必要。type-safety/general-language/proof/performance/securityはunsupported。global installしない。

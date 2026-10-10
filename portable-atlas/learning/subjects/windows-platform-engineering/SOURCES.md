# Windows公式locatorと模型への対応

確認日2026-10-05。以下2ページのWeb本文を取得確認。全API互換や実Windows成功ではなく、有限subsetを決める原典。

| ID / 一次資料・節 | 対応と除外 |
|---|---|
| API [CommandLineToArgvW](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-commandlinetoargvw), Remarksの2n/2n+1/non-quote rules / Important / Parameters | 模型のquoted modeとbackslash parity。full command line/argv[0]、empty string→exe、leading whitespace、Unicode、allocation/LocalFree、preceding pathの注意はこのunitでは実証しない。 |
| CRT [Parsing C command-line arguments](https://learn.microsoft.com/en-us/cpp/c-language/parsing-c-command-line-arguments?view=msvc-170), rules / literal table | 手計算tableの共通subset5例の出所。argv[0]が特別であること、paired quotes/unclosed rulesなどconsumerの違いを読む。表row6は模型から除外し、そのCRT出力をAPIの期待値へ流用しない。 |
| MODEL [作者の有限契約](SPEC.md) | ASCII tail/128char/balanced/adjacent除外は作者の制約。[parser](parser.py)実行はPython modelの証拠で、Win32 API callではない。 |

[手計算table](hand-table.json)→[input](cases.json)→[raw](evidence/raw.json)→[39 closed-form matrix](evidence/parity-matrix.json)→[UTC/環境/source/input/raw/SVG digests](evidence/run.json)→[integrity](evidence/integrity.json)。[oracle](oracle.py)はparserをimportしない。公式literal一致とMac模型の観測をWindows成功と呼ばない。

[COVERAGE](COVERAGE.md)に主要未教材concept/question、次4実験と公式locatorを整理。追加locatorは本文未確認として明記。

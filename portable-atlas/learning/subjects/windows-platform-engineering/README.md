# Windowsを学ぶ入口 — backslashとquoteは何を変える？

**実Windows API / CRT / VM未実行。** DarwinのPython標準libraryで、CommandLineToArgvWのbackslash/quote説明に基づく有限argument-tail模型を実行する。完全互換やWindows成功ではなく、全Subject完成でもない。

**前提 → 主要概念/仕組み:** commandline文字列とargv配列は異なる。quoted modeがspace/tabの分割を変え、quote直前のbackslash偶奇がtoggleとliteralを分ける。最終consumerがAPI/CRT/cmd/PowerShellかを区別する。[契約](SPEC.md)にASCII tail128、balanced/adjacent除外、argv[0]等の未実装を明示。

**今回の実装・正常/境界/意図異常:** [parser](parser.py)が模型をscanし、1charごとのstateとEOFを保存。正常subsetと単純Python splitを比較する。quote内space、odd/even slash、non-quote slash、empty argument、tail whitespace/tab、max128、subset外/入力拒否を21展示caseにした。[手計算table](hand-table.json)は公式CRT共通subset例と作者vector。CRTとAPIを同一仕様にしない。[独立oracle](oracle.py)はtable lookupと39個の閉形式parity期待値でparser scanを共有しない。

**予想 → 操作 → 比較 → 原典/実装 → 答え:** [UI](index.html)でquoted spaceが何引数か予想。case選択→次char/全char/reset→pending slash/quoted/current/emit済みargs/単純split/独立期待値を比較→原典/実装→答え。input拒否はtraceなし、subset拒否は途中stateを残し最終args=null。異常splitのtraceは説明用。

このdirectoryで:

```sh
python3 -B runner.py
python3 -B runner.py --input-json '{"tail":"a b"}'
python3 -B checker.py
python3 -B route.py quoting
python3 -B route.py windows-api
python3 -B preview.py
```

accepted exit0、input/subset拒否exit2。通常runner/checker/route/observeはread-only。原票更新は `python3 -B observe.py --write-evidence`、artifact bindingだけは `python3 -B checker.py --seal-evidence` を明示。通常検査失敗で原票を更新しない。入力tailをprocess/evalへ渡さない。

[raw](evidence/raw.json)、[parity matrix](evidence/parity-matrix.json)、[UTC/環境/source/input/artifact digests](evidence/run.json)、[実IAB QA/cleanup](evidence/ui-qa.json)、[integrity](evidence/integrity.json)、[検証結果](evidence/verification.json)。[quote図](evidence/quote-trace.svg)は生成SVG、IAB JPEGは実capture。previewはdynamic127.0.0.1のみ、確認後Ctrl-Cで終了。[教材内skill](skills/atlas-windows-platform-engineering/SKILL.md)は既存route、global installなし。

**実務判断:** quotingはconsumer依存。program名/tail/Unicode/shellを分け、実対象のcontractで検査する。full APIではleading whitespaceやempty commandlineに別の意味があるが、今回tailのleadingをskip・emptyを[]にした。subset外入力をWindows拒否と呼ばない。公式APIにはpathに関する注意もあり、ここで任意文字列のnative互換を保証しない。

**限界 → 次の学習 → 原典:** Win32/CRT/VM実行なし、Mac argvの成功を代用しない。full commandline/argv[0]、Unicode/adjacentquotes/shell/実process/security/UI/toolchainは未教材。[COVERAGE](COVERAGE.md)に主要概念の問いと次1: native consumer差、次2: handle/async、次3: token/ABI、次4: 実対象観測の4実験と公式locatorを整理。[SOURCES](SOURCES.md)で本文確認済みとlocatorのみを区別する。旧Goal/他module/旧Gate/OS設定/install/commit/push/公開を変更しない。

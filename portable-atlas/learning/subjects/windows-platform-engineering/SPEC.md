# 有限argument-tail quoting模型の契約

**実Windows CommandLineToArgvW / MSVC CRT / VM未実行。** Darwin上Python標準libraryの有限模型。Windows APIの完全互換・実Windowsでの成功を主張しない。[原典](SOURCES.md)と作者のsubsetを分ける。

入力は `{"tail":"..."}` の1keyのみ、string0..128文字、ASCII printable0x20..0x7Eとtab。bool/extra key/129文字/NUL/newline/Unicodeは教材input拒否。char数=ASCII byte数。これはWin32 Unicode APIの制限ではない。

**argument tailのみ:** 固定program名が既に取り除かれた場面を仮定し、出力は`args[0..]`（tailのindex）と呼ぶ。full command lineのargv[0]処理、実program path妥当性、full lpCmdLine先頭空白による空argv[0]、empty lpCmdLineがexe pathへなる動作は未実装。tailのleading/trailing whitespaceは無視しempty tailは[]。full APIのempty/leading挙動とは同じではない。

| 字符 / 条件 | この模型の操作 |
|---|---|
| backslash | pending countを1増やす。次charまで出力を保留 |
| quote直前に2n本backslash | n本をoutputし、quote自体をoutputせずquotedをtoggle |
| quote直前に2n+1本backslash | n本とliteral quoteをoutput、quotedをtoggleしない |
| backslashの次がquote以外/EOF | pending全数をliteralとしてoutput |
| space/tab、quoted=false | activeな引数をemit、繰返しseparatorをskip |
| space/tab、quoted=true | whitespaceをargument内へoutput |
| その他ASCII | literalとしてoutput。single quote/caret/metachar/環境変数展開なし |
| EOF、quoted=false | activeな最後のargumentをemit。empty quoted tokenも保持 |

standalone `""`（前後がtail境界/区切り）だけempty argumentとして許す。連続したsyntactic quotesのその他形（例CRTのadjacent quote rule、triple quotes、`a""b`）はsubset外で拒否。escaped literal quote直後のclosing quoteとは分ける。balanced quoteだけを対象としunbalancedはsubset拒否。**subset拒否はWindows/CRTがその入力を拒否する証拠ではない。** 実CRT資料のunclosed/pairedquote規則も未実装。

input拒否はtraceなし。subset拒否は失敗直前までの有限trace/stateを保持しargs=null（途中argument listを最終結果にしない）。正常traceは1charごとにquoted/current/pending/args/activeのbefore/afterを保存、EOFは別row。MAX128+EOFで有限。単純split異常は実Python `str.split()`の結果。異常側のchar traceは説明用に同じwhitespace splitを再生し、実Windowsのtraceではない。

[手計算table](hand-table.json)は公式CRTliteralの共通subset5例と作者vectorsを別記。CRTは別consumerであり、共通例が一致してもAPI等価とはならない。[独立oracle](oracle.py)は手記lookup、39個のbackslash0..12/quoted mode/非quote-runを閉形式で構成し、parserのscanを共有しない。chartraceには局所状態の検査も行う。

このunitはquoting理解の入口。cmd.exe/PowerShell/shellescape、CreateProcess、実UTF-16、Win32 allocations/LocalFree、kernel/security/GUI/実Windowsは未実装・未実行。tailをprocess実行やevalへ渡さない。

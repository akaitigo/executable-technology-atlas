# Expressions: 文字の順番と計算の順番

整数・`+`・`*`・括弧の独自grammarを、Python stdlibのlexer→再帰下降AST→tree評価として実装した有限教材です。通常checkerはread-only。保存runをUIでstep再生し、優先順位が違う木を作ること、error定位と評価停止を比較します。

## 問いと観測

`2 + 3 * 4`は文字を左から読むだけなら20になるかもしれません。しかし、宣言grammarでは14。`*`のsubtreeを先に評価します。括弧を付けると両経路20。比較用naiveは`+`と`*`を同順位・左結合にする意図的な別grammarで、括弧は尊重します。「文法として無効」ではなく期待するsemanticsからの逸脱です。

| input | 正常 | naive |
| --- | --- | --- |
| `2 + 3 * 4` | 14 | 20 |
| `(2 + 3) * 4` | 20 | 20 |
| `2 * 3 + 4 * 5` | 26 | 50 |
| `0007 + 0 * 999999` | 7 | 6999993 |
| `0` | 0 | 0 |

`2 + * 3`はoffset4 / line1 / column5、`(2 + 3`はEOF offset6、`2 + x`はlex offset4で停止。`2 +\n * 3`ではline2/column2。offsetはUnicode code pointの0始まり、line/columnは1始まり。原票は[evidence/run.json](evidence/run.json)、生tokens/AST/traceは[evidence/stdout.json](evidence/stdout.json)。

## 通常操作はread-only

Repository rootから:

```bash
cd learning/subjects/programming-languages-compilers-runtimes
python3 -B check.py
python3 -B check.py --expr '2 + 3 * 4'
python3 -B verify.py
```

checkerはstdoutのみ。custom inputにerrorがあるとstructured errorをstdoutへ出しexit2。固定10case batchはerror事例も教材観測として保存し、batch自体はexit0です。`observe.py`のoptionなしもstdoutのみで、原票を更新しません。

原票の更新を明示的に行う場合だけ:

```bash
python3 -B observe.py --write-evidence
```

新しいchecker subprocessのstdout/stderr、時刻、環境、input、source version/hash、SVG Artifact digestを記録し、`data.js`と図も更新します。これは検証Gateを成功扱いに変更するoptionではありません。更新後は`verify.py`とページreloadで確認します。

UIを開く場合:

```bash
python3 -B -m http.server 8798 --bind 127.0.0.1
```

<http://127.0.0.1:8798/> を開き、終了はCtrl-C。`index.html`の直接表示でも保存`data.js`を読めます。stdlib Python3.9以上だけ。install、Docker、外部サービス不要。UIは保存10 inputのtraceを再生し、任意入力を評価したりPythonを呼び出したりしません。

## 実装・oracle・原典

- [language.py](language.py)：ASCII integer token、span、expr/term/atom、explicit Group node、postorder trace。`eval()`/`exec()`/host ASTは不使用。
- [verify.py](verify.py)：手で固定したvalue/tree、独立regex lexerとiterative shunting-yard、token span、ASTとpostorderを照合。generated100例、invalid15件、Evidence mutation5件を検査。default/custom checkerとoptionなしobserveの3 processで全module byte不変も確認。独立経路ですが、外部reviewerや形式証明ではありません。
- [AST図](evidence/precedence-ast.svg)：実parser出力の再描画。実画面captureではありません。
- [Theodore Norvellの原著記事](https://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)：priority、AST、再帰下降とstack方式。
- [Robert Nystromの著者Repository / Scanning](https://github.com/munificent/craftinginterpreters/blob/master/book/scanning.md)：lexeme/token、error reporting。book siteのfetch失敗を受け著者Repositoryを使用。第三者本文や実装を保存・コピーせず[sources.json](sources.json)へlocatorだけ記録。

## 境界・状態

問いはpriorityがtokensからASTへどう表れるか、成功条件は実parser/traceと別oracleの一致、errorで評価が止まること、UIで比較できることです。integerは非負ASCII6桁、入力256 code point、括弧depth16まで。limits違反はgrammar semanticsそのものと別のresource boundaryです。

[COVERAGE.md](COVERAGE.md)は全分野の未教材範囲を列挙します。[実IAB QA](evidence/visual-qa.json)、[module内Skill routing](evidence/skill-routing-check.json)は別記録。global Skill installなし。ローカル教材単位の成果で、Portal／分野全体の完成や学習者理解度は更新しません。旧repo、Core/Graph、commit/push/公開なし。

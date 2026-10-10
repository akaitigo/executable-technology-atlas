# Technical Documentation / Architecture as Code

JSON契約から実Markdown・SVGを生成し、文書の鮮度、参照、実行例を別々に検査する有限教材。日本語UIは [index.html](index.html)。2関数・8例の正常/境界と意図異常を扱う。全SubjectやAtlasの完成を意味しない。

## 学習の道筋

1. 前提: JSONのlist/object、純粋関数、整数、SHA-256を読めること。契約は [contract.json](contract.json)、実装は [api.py](api.py)。
2. 主要概念: source of truth、決定的生成、source/artifact digest、local anchor、実行可能な例、独立期待値。鮮度と意味の正しさは別問題。
3. 今回の実装: [model.py](model.py) が契約から [api.md](generated/api.md) と [architecture.svg](generated/architecture.svg) を実生成する。[manifest](generated/manifest.json) がcanonical JSONとapi.pyのbytes、および各artifactをSHA-256で結ぶ。小JSONはOpenAPIではない。図は固定の生成工程図であり、全体設計の抽出ではない。
4. 正常/異常: UIで予想を書き、条件を操作、実stdoutと期待を比較、raw文書/原典/実装を確認して答えへ進む。
5. 実務判断: source不一致は再生成を促す。artifact一致でもanchor切れは拒否する。生成成功でも期待値が誤っていればsnippetは失敗する。「文書がbuildできた」だけで仕様との一致を断定しない。
6. 限界と次の実験を下のcoverageから選び、公式原典へ進む。

## 実行

このディレクトリでPython標準ライブラリのみを使う。新依存・Docker・公開・外部APIは不要。

```sh
python3 -B run.py --scenario baseline
python3 -B run.py --scenario stale-contract
python3 -B run.py --scenario regenerated
python3 -B check.py
python3 -B server.py
```

最後のコマンドが表示する127.0.0.1のURLを開く。終了はCtrl-C。serverは専用UI/APIのみを配信し、moduleや親ディレクトリを丸ごと公開しない。通常 [check.py](check.py) と [generate.py](generate.py) はread-only。保存生成物の更新は `python3 -B generate.py --write`、結果原票更新は `python3 -B check.py --record` を明示する。変更シナリオはメモリー上に作り、保存済み契約/実装は書き換えない。

| 条件 | 期待 | 判断できること |
|---|---|---|
| baseline | passed、8 stdout一致 | clampの下限外/下限/内側/上限/上限外、addの正/相殺/零 |
| stale-contract | stale-contract | 例の上限10→8に対して保存文書が古い |
| regenerated | passed、11→8 | 再生成された文書内snippetを実行 |
| stale-code | stale-code | 実装bytes変更（comment追加）も入力の鮮度を失わせる |
| broken-anchor | broken-local-anchor | artifact hashを更新しても索引のapi-missingは解決しない |
| unsupported-function | unsupported function | divideは契約の関数allowlist外 |
| wrong-output | snippet-output、期待6/実5 | 誤った契約期待値を再生成しても意味は正しくならない |
| tampered-svg | artifact-digest:architecture.svg | 生成後のSVG手編集を検知 |

生成Markdownから限定fenced Python例と期待stdoutを抽出する。契約から組み立てた認識可能なコードと完全一致したものだけをsubprocess `python -B -c` で実行する。任意入力のコード実行機能ではない。整数は±100、clampは3引数と下限≤上限、addは2引数。型違い、過大範囲、重複関数、未対応schema/関数/例は拒否する。引数省略、汎用Markdown parser、全CommonMark構文は未対応。

## 独立検査と証拠

[oracle.py](oracle.py) は生成器をimportせず、8条件のstatus/failure/実stdout固定表、公式locator固定表、SVG XMLの3ノード/2辺/ラベル、明示anchorの期待位置を照合する。checkは別の整数走査によるAPI期待値と、source/artifact hashの独立再計算も行う。hashは「最新か」「改変されていないか」の証拠であって署名・信頼・説明の妥当性を証明しない。generator自体の変更は [evidence/bindings.json](evidence/bindings.json) に結ぶ。

[evidence/run.json](evidence/run.json) に実行時刻/環境/command、入力、raw Markdown/SVG/snippet source/stdout/stderr/exitCode、独立期待、source/artifact/input/raw digestを保存。[evidence/ui-qa.json](evidence/ui-qa.json) に実HTTP IAB操作と画面観測を記録する。画面captureの実取得・保存可否はこの原票に分けて記す。架空の画面や再描画をcaptureとして扱わない。Skillの [SKILL.md](skills/atlas-technical-documentation-architecture-as-code/SKILL.md) はrunner/checker/UIの案内だけを担う。[routing-smoke](evidence/routing-smoke.json) は主agentによる実コマンド確認で、独立forwardAgentEvalではない。

## 未教材coverageと次の実験

| 概念・問い | 次に作る実験 | 公式locator |
|---|---|---|
| API仕様/互換性: 型・エラー・deprecationを変えると利用者は壊れるか | 旧新版contract差分と互換/非互換の利用例を実行 | [OpenAPI](https://spec.openapis.org/oas/latest.html) |
| 情報設計/文書build: tutorial/how-to/reference、翻訳、検索、accessibilityをどう支えるか | 複数ページのcross-reference切れと翻訳の鮮度をbuildで検査 | [Sphinx cross-reference](https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#cross-referencing-arbitrary-locations)、[Diátaxis](https://diataxis.fr/) |
| architecture/判断: context/container/componentとADRの理由・代替案は合うか | 小ADRから依存方向を検査し循環と古い決定を注入 | [C4 model](https://c4model.com/)、[ADR](https://adr.github.io/) |
| 再現性/配布: generator/runtime/環境変更を追跡できるか | 二環境build差分、provenanceと改変manifestを比較 | [Reproducible Builds](https://reproducible-builds.org/docs/)、[SLSA provenance](https://slsa.dev/spec/v1.2/provenance) |

実用のOpenAPI/Sphinx/C4/ADR toolchain、複数言語生成、CI配布・署名、任意コードsandbox、設計妥当性のレビュー、Site/publicationは未実装。Core `atlas audit` と `npm run gate` は専用moduleの今回scope外で未実行。全Subject完成は主張しない。Goalは作成しない。

## 原典と今回の対応

- [Python doctest: how it works](https://docs.python.org/3/library/doctest.html#how-it-works): 文書内の例と期待出力を実行して照合する発想。本教材はdoctestを呼ばず限定形式のsubprocess runnerを実装。
- [CommonMark fenced code](https://spec.commonmark.org/0.31.2/#fenced-code-blocks): fenced codeの構文。本教材の抽出器は限定形式のみ。
- [W3C SVG svg要素](https://www.w3.org/TR/SVG2/struct.html#SVGElement): generated SVGの構造とviewBox。設計図の意味の正しさまでは仕様で決まらない。
- [ADR](https://adr.github.io/): 判断の記録と背景。今回の生成工程にADR機能はない。

公式ページは制作時に実取得確認。全文を複製しない。最新URLの内容は変わり得る。locatorsは固定表で検査する。

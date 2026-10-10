---
name: atlas-programming-languages-compilers-runtimes
description: 整数・加算・乗算・括弧の独自grammarをtoken→AST→評価へ追い、優先順位と構文errorを比較する有限ローカル教材。実言語compilerやJIT/ABIの検証には使わない。
---

# Bounded expression教材

このdirectoryの`../..`が教材root。[README](../../README.md)で入口、[Coverage](../../COVERAGE.md)でgrammarとlimitsを確認する。

- 保存結果は[run](../../evidence/run.json)と[raw tokens/AST/trace](../../evidence/stdout.json)へroute。時刻・環境を添え、未再観測を現在の実測とは呼ばない。
- custom inputは教材rootで`python3 -B check.py --expr '2 + 3 * 4'`、保存原票の検査は`python3 -B verify.py`。通常checker／optionなし`observe.py`はstdoutのみでread-only。errorのcustom実行はexit2。
- 原票更新を明示依頼された場合だけ`python3 -B observe.py --write-evidence`、その後verifyとUI reload。自動で原票を書き換えて検査を合わせない。
- [UI](../../index.html)で予想→tokens→AST build→postorder→naive比較／errorへ進む。[language.py](../../language.py)は実装、[verify.py](../../verify.py)は別stack/tree oracle。[図](../../evidence/precedence-ast.svg)は実parserの再描画でcaptureではない。

Naiveはpriorityをなくす意図的別grammar。error時の値なしと正常0を混同しない。offset0始まり／line,column1始まりを説明し、byte offsetへ置換しない。

型・functions・実compiler・JIT・ABI・最適化・任意grammarの依頼はこの教材の未対応を具体化する。新依存、外部サービス、設定変更、global Skill install、公開へ範囲を拡張しない。

# ローカルSkill routing review

2026-10-05にCodexが自己レビュー。独立Agent forward evalではない。対象はこの有限OLS教材の既存runner／checker／UIのみ。

`quick_validate.py skills/atlas-data-science-statistical-learning`の実結果：`Skill is valid!`。

## 実行した2経路

観測時刻：`2026-10-05T06:01:43.073289+00:00`。

| 問い | 実route | 実結果／回答境界 |
|---|---|---|
| trainだけで学習した係数と評価誤差は？ | `/usr/bin/python3 -B lesson.py --case train-only` | exit 0。切片1、傾き1.8、train MSE 0.31999999999999995、holdout MSE 4.32。holdoutをfit/selectionへ使っていない。固定追加評価MSE 322.82666666666665であり現実の汎化保証ではない。 |
| random forestの性能も同じrunnerで調べて | `/usr/bin/python3 -B lesson.py --case random-forest` | exit 2。未対応を明示し、固定3候補をrandom forestへ置換しない。READMEの未教材Coverageへrouteする。依存導入は行わない。 |

未対応routeの実stderr：

```text
usage: lesson.py [-h] [--record]
                 [--case {train-only,fit-leakage,selection-leakage,exact-line,two-points}]
                 [--port PORT]
lesson.py: error: argument --case: invalid choice: 'random-forest' (choose from 'train-only', 'fit-leakage', 'selection-leakage', 'exact-line', 'two-points')
```

正常の原票は[Python観測](python.json)、[実HTTP応答](http.json)にsource／data digestとともに保存。混入fit・候補選択の警告、予想の一致／不一致、2点境界、一定x／空／JSON拒否と回復は[実UI DOM](ui-dom.json)で確認した。

Skillは既定checkerへread-only routeし、`--record-*`を原票更新が必要な場合だけに限定する。Skillに新方式・外部Runtime・公開・他Repository変更の権限はない。READMEとUIに学習の道筋、実務判断、4つの未実行次実験、一次資料と未教材領域があり、全Subject完了は主張しない。

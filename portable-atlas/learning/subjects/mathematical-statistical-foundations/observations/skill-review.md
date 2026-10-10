# 限定Skillの確認記録

2026-10-05、Codexによるlocal read/controlと自己レビュー。独立Agent、global install、全Subject評価は実施していない。

実行: `python3 skill-creator/scripts/quick_validate.py skills/atlas-mathematical-statistical-foundations` → `Skill is valid!`。これはfrontmatter/namingの形式確認であり、回答品質全体の評価ではない。

教材rootでMac標準Pythonから既存`lesson.calculate(PRESETS[name])`を実行した。

| 依頼例 | 実際の操作 / 観測 / routing |
|---|---|
| 「Aが1%の表で感度とPPVを比較して」 | `calculate(PRESETS['rare'])`を実行。感度`9/10`、PPV`1/12`、PPV分母108。Skillの実装/原票リンクから操作可能 |
| 「test+が0ならPPVも0と返して」 | `calculate(PRESETS['no-positive'])`を実行。感度`0`、PPV`None`、分母0。未定義を0へ変更しない |
| 「12要素を手で数えて確認して」 | `calculate(PRESETS['hand-count'])`を実行。感度`2/3`、PPV`2/5`、分母5。8unittestの独立手書きラベルfixtureもPASS |
| 「未知の母数の信頼区間を出して」 | Skillとscopeをlocal read。sampling/推測統計は未対応と返し、既知populationの割合計算と区別する。新しい推定処理は実行していない |
| 「この合成表で現実の個人の状態を判断して」 | Skillとscopeをlocal read。現実のpopulation ratesと個別判断を検証していないため、この教材では未対応と返す |

正常/分母0/手数えの行は実runnerによる観測。未対応の行は指示と実装の自己レビューであり、別Agentが実際にroutingした証拠ではない。新しいSkill専用scriptは作らず、既存moduleを再利用した。

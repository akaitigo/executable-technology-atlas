# Skillの限定動作確認

2026-10-05、Codexによるlocal read/controlと自己レビュー。独立Agent評価、global install、browser/runtime全再走は実施していない。

`python3 skill-creator/scripts/quick_validate.py skills/atlas-computational-mathematics-numerical`の結果: `Skill is valid!`。validatorはfrontmatter/namingを検査するもので、内容や全質問への回答品質を証明しない。

| 依頼例 | 実際に確認した操作 / 応答 | 判定範囲 |
|---|---|---|
| 「1,2,3,4を各方法で比較して」 | `lesson.experiment(['1','2','3','4'])`を実実行。oracle 10、4方法とも10.0。checker/source/原票リンクを辿れる | 既存runnerによる正常入力 |
| 「1e16,1,-1e16ならKahanで必ず1？」 | 同runnerで実実行。naive 0.0、Kahan 0.0、Neumaier 1.0、fsum 1.0、oracle 1。Skillの境界説明と一致 | この入力の実測だけ。Kahan万能とは返さない |
| 「PythonとJSの精度が同じと証明して」 | SkillとUI実装を読み、JSはPython結果の表示・図の座標化だけと確認。「JS総和比較は未測定」と返す | local readによる境界確認。JS総和の実行証拠はない |
| 「このコードでODE solverを作って精度保証して」 | このSkillでは未対応と返す。READMEの未教材scopeへ案内 | local readによる用途確認。ODE solverを作成・実行していない |

実計算コマンドは教材rootで`/usr/bin/python3 -B`から`lesson.experiment`をimportする小さなlocal control。今回の2入力の結果は上表へそのまま転記した。Skill用の新しいrunnerやresource実装は作らず、既存moduleを使った。

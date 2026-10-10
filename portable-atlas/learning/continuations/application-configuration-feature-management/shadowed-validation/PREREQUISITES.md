# 前提と読む順

JSONの数値・boolean・文字列、辞書、優先順位を前提にします。例えばfalseと0はJSON型が違い、"false"は文字列です。default→env-input→task-jsonの後の層が同じfieldを上書きします。今回は4field固定で、隣のfieldの上書きは不正値を修復しません。

元subjectは型・優先順位・由来・actor rolloutを扱います。atomic-reload-snapshotは、採用した版を要求途中で混ぜないという更新/読取の問題です。今回の問いは「採用前にどのlayerを型検証するか」で、更新並行性やrolloutは再実験しません。

出所の場所は共有repoの `learning/subjects/application-configuration-feature-management/README.md` と `learning/continuations/application-configuration-feature-management/atomic-reload-snapshot/README.md`。この単体HTTPの外にある場所なので、画面内で成功するリンクとは扱いません。必要な規約を[契約](CONTRACT.md)へ要約し、出所hashを[保存記録](records/reuse-and-sources.json)へ固定しました。

[README](README.md)から条件を選び、候補raw、検査した値、公開configを順に読みます。全層で拒否した同じ入力を勝者だけへ切り替え、下位の不正を検査していないことを確認して[Skill](SKILL.md)へ戻ります。

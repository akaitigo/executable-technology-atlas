---
name: atlas-agent-resume-uncertainty
description: Atlasの有限な再開記録で、承認消費と効果完了の知識を分ける。実操作の許可や復旧実行には使わない。
---

# Atlas｜承認と再開判断を読むSkill

[読む順](README.md)→[契約](CONTRACT.md)→[画面](index.html)→[原典と既存実装](SOURCES.md)→[範囲](COVERAGE.md)を使います。[手期待](expected.json)と[保存計算](observations/run-01/results.json)を分け、[状態](qa/reader-acceptance.json)で実施範囲を確認します。保存計算のcase IDは、中央2件が `consumed-before-effect` / `effect-without-result`、期限切れが `ready-expired`、完了が `completed` です。

1. 「承認消費済みなら操作も済んだ？」には中央2条件を案内する。同じ入力bytesに対して、復旧側の判断はUNKNOWNのまま。observerが知る効果0/1を復旧側が知っていたとは説明しない。
2. 「もう一度動かして効果が1件なら安全？」には消費を戻す故障対照を案内する。効果1／2の違いと、両方で承認再利用になることを分ける。[具体callへの承認](related.html?topic=authorization)へ戻り、新しい承認の必要性と効果の確認を混同しない。
3. 「期限切れだから保存結果も消す？ 自動復旧できる？」には未消費・期限切れと完了記録を比較する。新規dispatchの認可と、保存結果を読む操作を分ける。実照会・補償・再承認・exactly-onceには回答を広げず、[既存APIの再送契約](related.html?topic=api)と未対応へ戻す。

予想→保存結果→対照→原典/実装→答え→限界の順を保ちます。この3例から保存結果・前提・原典・限界へ辿る読取利用を独立確認しました。画面のSkillリンクも実pointerで開き、本文を確認しています。これを一般Agent評価や実復旧の保証へ換算しません。このSkillから実外部操作・新規サービス・OS設定変更を開始しません。

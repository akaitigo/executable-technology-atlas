---
name: atlas-workflow-retry-readiness
description: Atlasの固定B→D模型で、失敗分類・残る追加試行予算・再開可能時刻の合同判断を案内する。実Airflowや外部要求、実障害の自動分類には使わない。
---

# Atlas — 再試行の問いを比較へつなぐ

[README](README.md)と[前提](PREREQUISITES.md)から始める。現在の実行・画面確認状況をREADMEで確認し、未実行の予想を観測済みと説明しない。

- 「予算が残るなら何でも再試行できるか」にはnonretryable-stopを案内する。PERMANENTは今回の方針で非対象で、SUCCESSという未到達の入力を先読みして再試行を正当化しない。
- 「再試行が予定されたら、すぐ始められるか」にはretryable-resumeの失敗完了t=1、due=3、t=2/3の対照へ。dueは失敗開始ではなく完了から計算する。時刻条件と実schedulerの即実行を分ける。
- 「retry2は全部で何回か、いつ減るか」にはretry-budget-exhaustedへ。初回を含む3試行、追加開始時の残数2→1→0、最後の失敗後に新dueを作らないことを手表で確かめる。上限の原理自体は既存教材へ戻す。
- 「失敗を見た下流は直ちにblockedか」には正常とpremature-downstream-blockを比較する。既存のpending/最終blocked規則を再利用し、Bが回復しても故障版のDは実行0であることを読む。
- 「POSTや業務処理を安全に再送できるか」には[前提のAPI再送](PREREQUISITES.md)へ戻す。pure計算の今回の結果で副作用の重複防止を証明しない。

予想→保存結果の操作→正常/終端失敗/故障比較→[原典対応](SOURCE-MAP.md)・[固定契約](CONTRACT.md)・[手表](hand-oracle.json)→答え→実務判断の順に案内する。未知の失敗分類、実workerの導入、外部送信、設定変更をこのSkillだけで行わない。[範囲](COVERAGE.md)に残る製品・実時間・永続化の検証へ一般化しない。

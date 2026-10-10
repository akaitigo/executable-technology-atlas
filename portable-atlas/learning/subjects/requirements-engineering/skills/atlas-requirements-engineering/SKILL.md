---
name: atlas-requirements-engineering
description: この有限queue教材で要求ID・revision・実テスト・Evidenceの対応、orphanとstaleを実行比較する。要求獲得や人の承認、要求工学全体の完成には使わない。
---

# 要求traceabilityの有限教材

このSkillの2階層上が教材root。README.mdの比較条件と未教材範囲を確認してから、既存runner／checker／UIだけを使う。新しいFramework、Graph、外部サービス、依存やOS設定を追加しない。

- 要求とtestの対応を学ぶ: `python3 -B runner.py --case normal`、比較は `boundary`／`orphan`。
- 変更後も旧テストが緑という問い: `stale-revision` → `retested-revision`。旧Proofを削除せず拒否理由と現在Evidenceを比較する。
- 不具合でtraceabilityと挙動を分ける: `broken-queue`。実overflowを見て、2/3のfinite Coverageと独立oracle一致の意味を説明する。
- チェックは `python3 -B test_runner.py`。通常は読取のみ。生観測の保存を依頼された場合だけ `--record` を追加する。
- UIを求められた場合だけ `python3 -B serve.py --port 0` で専用loopbackを起動し、出力URLで実操作する。自分のserver／tabを終了する。権限拒否をfile URL等で迂回しない。

予測→操作→比較→公式locator／実装→答えの順で案内する。pass表示だけで説明せず、要求ID／revision／内容、app/config・harness digest、operation before/output/after、拒否された旧Evidenceを照合する。

要求獲得・本番の要求承認・一般的なSLO／規制認証・外部queueはunsupported。この教材の6ケースへ無理に置換せず、未教材であることとREADMEの次実験候補を示す。実利用者の意思決定を生成しない。3/3は有限matrixのみで、人の承認やSubject全体の完成を意味しない。

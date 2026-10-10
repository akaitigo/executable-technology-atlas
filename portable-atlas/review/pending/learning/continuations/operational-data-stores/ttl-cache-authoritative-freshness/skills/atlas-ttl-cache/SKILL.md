---
name: atlas-ttl-cache
description: このsingle-key SQLite原本とfake-clock cache教材を再実行し、期限とharness鮮度を監査する。実RedisやHTTPキャッシュの検証には使わない。
---

rootはこのファイルから `../..`。[README](../../README.md)、[事前手表](../../EXPECTATIONS.md)、[範囲](../../COVERAGE.md)を読む。適用AGENTS/admissionを確認。通常再現はrootで `python3 -B runner.py`、保存監査は `python3 -B checker.py` と `python3 -B test_negative.py`。これらはread-only/memory-only。新しい採取を依頼された場合だけ `runner.py --record` を明示し、失敗原票を保持して成功rawだけcurrentへ昇格する。

専用dynamic loopbackで `python3 -B server.py`、専用tabのindexを開く。予想→fixture/TTL/policy操作→実SQL比較→event stepの再表示→client/harness/SQL raw→原典/source→答え。全15固定＋4編集をliteral/oracleへ照合、条件/全予想入力reset、拒否、503、保留古い応答の破棄、native capture、文書/Skill viewerを確認する。UI比較は実子processのSQLを再実行するがevent stepは実行済timelineの表示。実clock観測とは呼ばない。

strictはt<expires_at、inclusiveは故障対照。fill/refill時刻+TTLへ期限再設定する。原本UPDATEでcacheを勝手に更新しない。cache hitのclientは原本auditを知らず、harnessだけがversion/value staleを比較する。valueが同じでもversion差を消さない。空cacheのhit分母は未定義。clock逆行、bool、TTL不正、未知keyはSQL前に拒否。

新採取のUTC/sourceSHA/request receipt/SQL trace/rowsを保存し、通常CLI前後SHA・mtime不変を確認。自分のtab/serverだけ終了し、開始時の保護listenerを維持する。old artifactやaccepted単位を変更しない。global install、公開、commit/push、実Redis/Cloudflare、負荷、stampede、eviction、OS設定・課金を含めない。未観測や模型の仮定を全cache保証へ広げない。

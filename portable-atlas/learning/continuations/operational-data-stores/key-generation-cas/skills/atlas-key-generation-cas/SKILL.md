---
name: atlas-key-generation-cas
description: 有限SQLite教材でversion-onlyとgeneration付きCASを比較し、key再作成の旧要求と入力拒否を検算する。分散CASや本番durabilityの保証には使わない。
---
この単元のREADME、contracts.jsonを読む。route.pyの7入口へ依頼を対応づけ、保存UIで予想→操作→rowcount/state→答えを比較する。
checker.pyは手書き状態表とDB snapshotの読み取り検算。通常runnerは書かず、再記録の明示依頼時だけrunner.py --recordを使う。専用tmp DBはrunnerが生成・close・snapshot保存後にcleanupする。
同世代のversion不一致と、key lifetimeの変更を分ける。g1/g2の非再利用はこの合成scheduleの契約で、分散発行器の実証ではない。
0行更新はSQL成功時のWHERE不一致。expected-refusalはUPDATE前の型境界、expected-sql-errorはSQL失敗probeとして別に扱う。
分散CAS保証、backup復旧のgeneration重複防止、電源断、並列lock性能は未対応。READMEの未実行coverageへ案内し、実service・権限・公開・課金をこのSkillから推定しない。

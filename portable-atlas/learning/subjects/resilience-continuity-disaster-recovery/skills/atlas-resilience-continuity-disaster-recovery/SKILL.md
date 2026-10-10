---
name: atlas-resilience-continuity-disaster-recovery
description: このmoduleの専用SQLite backup・restore教材を既存runner/checker/UIで学び、staleとcorruptを比較する。実データ復旧や製品DRには使わない。
---

moduleルートはこのfileから../../。README.mdでsynthetic tickと観測durationの限界を読んでから操作する。

- 実cycle：`python3 -B runner.py --case fresh`。caseはfresh/stale/corrupt/missing-backup/empty/stale-emptyだけ。独立oracle.pyとrawを比較する。
- 保存証拠の検査：`python3 -B checker.py`はread-only。原票更新を依頼された場合だけ`--record`。既存専用artifactを置換する。
- UI：`python3 -B server.py`の表示する127.0.0.1動的portを開く。予想→case操作→timeline/行/hash比較→原典→答え。終了時は自分のserverとtabを閉じる。

入力pathは追加しない。外部DB、実サービス、cloud DR、全durability保証、他moduleの依頼は未対応と伝える。sourceArtifact digestとQAを確認し、ローカルcopy時間をサービスRTO達成へ読み替えない。

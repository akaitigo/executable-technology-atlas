---
name: atlas-cloud-architecture
description: このmoduleの架空2zone graphと全故障matrixを既存runner/checker/UIで学び、共通依存とreplicated readを比較する。実cloud設定やSLA判断には使わない。
---
module rootはこのfileから../../。README.mdで二値故障・複製済みread・独立確率とsynthetic latencyの仮定を読む。
- `python3 -B runner.py --case dep-a`。対応caseはfixture.jsonの10caseのみ。rawのblockedNodes/selectedPathとoracle.pyを比較。
- `python3 -B checker.py`はread-only。明示的な原票更新依頼のときだけ`--record`。
- `python3 -B server.py`の一時127.0.0.1動的portで予想→操作→diagram/matrix→原典→答え。自分のserver/tabを終了。
製品実行、resource作成、価格、SLA保証、他moduleは未対応。新しい入力pathや外部設定を加えず、固定availability確率と実測uptimeを混同しない。

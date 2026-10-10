---
name: atlas-platform-engineering-developer-experience
description: このmoduleのtask-owned template/contract教材を既存runner/checker/UIで操作し、決定的renderとversion driftを比較する。実platform導入や外部project作成には使わない。
---
module rootはこのfileから../../。README.mdの固定contractと未実証境界を読む。
- 実render：`python3 -B runner.py --case cedar`。caseはfixture.jsonの10caseだけ。old-templateは決定的でも不適合になる。oracle.pyの手書き期待treeとdiffを比較する。
- 保存証拠：`python3 -B checker.py`はread-only。明示的に原票更新を依頼された場合だけ`--record`。
- UI：`python3 -B server.py`の127.0.0.1動的portで予想→操作→tree/hash/diff→原典→答え。自分のserver/tabを終了する。
生成はmodule内使い捨てfixtureだけ。入力pathやgit init、外部repo、saved project、global installを追加しない。実company platform、Backstage実行、認証認可、他moduleの依頼は未対応と説明する。

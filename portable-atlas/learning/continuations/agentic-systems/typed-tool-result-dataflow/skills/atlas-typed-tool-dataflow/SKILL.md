---
name: atlas-typed-tool-dataflow
description: 固定read/add教材でtool resultのtyped field参照、欠損・型・未知参照・cycleの拒否位置とdata/instruction境界を調べる。実LLM攻撃防御、外部tool、実承認や本番agent評価には使わない。
---

教材rootはこのdirectoryから ../..。READMEの契約を読み、unknown/cycleはpreflightでcall0、missing/string/boolはread後binding拒否でcall1を分ける。

保存証拠にはrootで `python3 -B skills/atlas-typed-tool-dataflow/route.py typed-reference`。独立checkerと採用rawを読み、normal=7とproposed_plan保持、badのviolationも報告する。値7だけで契約成功としない。

再現は `runner.py --case normal` または `server.py` の固定条件。新原票保存は明示 `--record` のみ。通常checker/routeはread-only。fixtureへ任意programや外部URL/credentialを追加しない。

llm-agentや実attack保証は未対応としてREADMEの未教材へroute。著者fixtureは人の承認証明ではない。新planをtool dataから選ぶbad comparisonは示しても実運用へ適用しない。

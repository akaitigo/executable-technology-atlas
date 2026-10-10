---
name: atlas-software-supply-chain
description: このローカル教材でSHA-256、合成build来歴、独立baselineとすり替えを実file原票で比較する。署名/SBOM/CVEやproduction supply chainの監査には使わない。
---

Module rootはこのfolderから `../..`。問いに必要な原票・実装だけ読む。

- 視覚教材は [index.html](../../index.html)、手順と信頼仮定は [README.md](../../README.md)。予想→変更→checksum/input/baseline比較→一次資料・実装→答えへ案内する。画面は保存済み実結果の再生。
- [observation-data.js](../../observation-data.js) の `directory` に現在runの `observation.json`、`command.json`、`artifact-index.json` と8 Scenarioの生artifact/manifest/source/依存configがある。観測時刻・版・input・command・exitを使って説明する。
- [pipeline.py](../../pipeline.py) はcanonical JSON buildと照合。別code pathの [verify.py](../../verify.py) をmodule rootで `PYTHONDONTWRITEBYTECODE=1 python3 verify.py` と実行すると、保存済みfileのhashと来歴bindingを検算できる。これは新buildではない。
- 新しい合成実生成を依頼された場合だけ、module rootで [observe.py](../../observe.py) を `PYTHONDONTWRITEBYTECODE=1 python3 observe.py` と実行する。元runを残す。package installや外部registryは不要。

checksum一致はauthenticity/署名証明ではない。ArtifactとManifest同時変更は自己整合を通せる。独立pinを保持したbaseline照合と、受け取ったbaselineからpinを作り直す危険な反例を区別する。input hash一致もbuild実行identityを証明しない。初期baselineへの拒否を更新の悪意と断定しない。

[sources.json](../../sources.json) のSLSA v1.2/OCI v1.1.1公式locatorへ戻る。署名・SBOM・package resolution・CVE・production registry・SLSA level・全toolchain再現性は未対応/未実証と返す。署名済・全Subject完成・理解度達成を宣言せず、global install・別repo・Core/Graphをこの入口から追加しない。

---
name: atlas-oci-container-engineering
description: このローカル教材のOCI object・2層tar読取と仮想path mapで上書き/whiteout/拒否を比較する。container起動や隔離・全OCI適合監査には使わない。
---

Module rootはこのfolderから `../..`。必要な原票と入口だけ読む。

- [index.html](../../index.html) で予想→object照合→tar生成入力→実読取map→原典/実装→答えを案内。[README.md](../../README.md) が手順・実結果・subset境界。画面は保存済み実結果の再生で、新しい生成を行わない。
- [observation-data.js](../../observation-data.js) の `directory` が現在run。`command.json`、`observation.json`、`artifact-index.json`、各caseの`input.json`/`result.json`/OCI layoutを使い、時刻・host・Source digest・生tarと結果を区別する。
- 保存fileの検算はmodule rootで `PYTHONDONTWRITEBYTECODE=1 python3 checker.py`。別code pathの [checker.py](../../checker.py) はread-onlyで、producer/consumerをimportしない。hashlib/tarfile自体は同じstdlib。
- 新規原票更新を明示依頼された場合だけ [runner.py](../../runner.py) の `PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record`。通常はchecker。既存run・失敗を残し、勝手に観測を更新しない。依存install/Docker/registryは不要。

[oci_subset.py](../../oci_subset.py) は実tar memberをbytesとして読むが、ホストへextractしない。仮想mapを実container/rootfs/mountと呼ばない。同層fileとlower-only whiteoutを分け、opaque/symlink等の未対応拒否を「OCIで禁止」と一般化しない。digest一致を署名や作成者証明にしない。configのlinux/amd64と実host identityを混同しない。

[sources.json](../../sources.json) のOCI v1.1.1公式locatorへ戻る。実container、namespaces/cgroups、隔離、opaque実装、圧縮layer、file属性、multiarch、registry、署名/SBOM/CVEやproduction証明は未対応/未実証と返す。全Subject/理解度完成を宣言しない。global install、別repo、Core/Graph、OS設定、GitHub操作をこの入口から追加しない。

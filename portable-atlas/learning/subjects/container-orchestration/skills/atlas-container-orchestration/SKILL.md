---
name: atlas-container-orchestration
description: このmoduleの2node有限配置モデルでreplica調整、故障再配置、Pending、容量を無視するbad実装を実観測と比較する。実Kubernetes運用やdeployには使わない。
---

# 合成配置を独立検算と比較する

教材rootはこのfileから`../../`。[README](../../README.md)で学習の道筋、境界、未教材を読み、[UI](../../index.html)で予想→入力→event→配置/oracle→原典/実装→答えを進む。Boundは合成node割当で、実PodのRunning/Readyではない。

- 通常はrootで`PYTHONDONTWRITEBYTECODE=1 python3 checker.py`。read-onlyで[保存済み観測pointer](../../observation-data.js)と原票を検査する。producerをimportしない独立enumeration/invariant oracle。
- 故障ならnode-failure-fit/node-failure-pending/node-recoveryへRoute。health入力、before/after配置、unbind/filter/bind/Pending events、最大配置数、healthy survivorを照合する。
- 「全部配置できた」ならover-capacityとbad-over-capacity、node-failure-pendingとbad-failureを対にして、capacity違反/independent rejectedを比較する。badのbound自己申告を成功にしない。
- revision/invalidならstale-revisionと型/ID/topology拒否の原票を照合する。通常checkerとUIは何も再配置しない。
- 新観測を明示依頼された場合だけrootで`PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record`、その後checker。旧runは削除しない。
- 実装は[model](../../model.py)、実file経路は[experiment](../../experiment.py)、一次資料と未教材は[sources](../../sources.json)へ戻る。

「kubectl apply」「本番clusterを直す」「Podへ通信」「PVCデータ復旧」はこの有限moduleで未対応と説明し実操作を始めない。slotモデルの結果を製品実証へ流用せず、READMEの次の実験/公式locatorへ案内する。未知Queryを既存caseへ無理に当てはめない。module-localのみでglobal install/permission追加は行わない。

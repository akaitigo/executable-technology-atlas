---
name: atlas-sensitivity-residual
description: 固定非特異2×2のb摂動で感度・残差・2oracleへのforward errorを分ける。任意solver安定性、性能、GPU、特異系解法へは使わない。
---

rootは ../..。READMEの前提/読む順番と事前表を読む。正常2・故障判断1・ε0契約拒否1を分ける。normは∞、残差はAx−b。

rootで `python3 -B skills/atlas-sensitivity-residual/route.py sensitivity-residual` は保存原票をread-only照合。新実行はrunner.py --case またはserver.py UI。新原票は明示runner.py --recordのみfresh UTC保存。

元xとの差を摂動後oracleへのforward errorと混同しない。十進oracle・実float A/bからのoracle、float残差・厳密再評価残差、元系・摂動後系を別に読む。残差小だけで元解への近さを判断しない。

general-solver / GPU / singular / arbitrary-matrixは未対応、READMEの境界と次案へroute。既存source/全Gateへ書込しない。

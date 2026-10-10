---
name: rollback-data-compatibility
description: 保存artifact rollbackとSQLite schema/data互換性の証拠を読む・照合する・明示時のみ新規観測する。
---

このmoduleだけを対象とする。既存runner/checker/UIへrouteする。
`python3 route.py inspect` はread-only checker、`python3 route.py lesson` はUIと原記録位置。
利用者が新規記録を明示したときだけ `python3 route.py record`。新runを追記し旧rawを保つ。
未知routeはexit 2。元Subject、Portal、実deploy、外部CI、Docker、global Skillは対象外。
artifact bytesのdigestとschema/data互換性、合成health failureを区別する。backup restoreや無停止保証を捏造しない。

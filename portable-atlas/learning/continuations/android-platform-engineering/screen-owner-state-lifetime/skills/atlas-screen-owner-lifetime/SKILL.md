---
name: atlas-screen-owner-lifetime
description: Androidのscreen ownerとview/stateの寿命を有限Python模型で比較する教材。実Androidや保存APIの検証には使わない。
---

# owner寿命の有限比較

../../README.md と ../../EXPECTATIONS.md を先に読む。lifetimeは ../../producer.py、compareは ../../index.html、verifyは ../../checker.py、sourcesは ../../SOURCES.md へ ../../route.py でroute。固定owner/view/state表をproducerから独立した期待値として照合。

通常コマンドはread-only、保存要求だけ明示 --record。Activity/process→owner→保存codecの順。rotate保持、finish除去、新create0、death消去を区別。拒否/nullと正常空ownerは別。全入力変更で旧答え本文を空にして閉じ、新値を保持する。

android、compose、savedstatehandle、sdk-install、process-killはunsupported。実OS再開やAndroid callback、永続性を証明したと扱わない。元Subject/共有Portal/旧教材・Core/fullGateは変更しない。

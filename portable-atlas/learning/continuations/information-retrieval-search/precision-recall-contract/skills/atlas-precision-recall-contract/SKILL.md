---
name: atlas-precision-recall-contract
description: Boolean返却集合の実装一致と合成relevanceに対するprecision/recallを既存runnerとUIで区別する。
---

# 案内

precision、recall、labels、boolean、undefined、retrieval-qualityの問いは[README](../../README.md)、[UI](../../index.html)、[route](../../route.py)へ案内し、単元で`python3 verify.py`を実行する。旧rawを上書きしない。scan/index一致をquality100%と呼ばず、分母0とlabelなしを区別する。

[原典](../../sources.json)と[coverage](../../coverage.json)へ接続する。ranking/ユーザー研究/製品/性能は未対応。依存追加/課金/global Skill/旧単元変更を行わない。

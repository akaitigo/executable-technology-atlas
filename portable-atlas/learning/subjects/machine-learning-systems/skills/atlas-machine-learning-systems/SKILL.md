---
name: atlas-machine-learning-systems
description: 固定numeric model artifactとschema/version入力のローカル推論を再現し、feature順序のsilent wrong、契約拒否、固定batch記述統計を比較する。学習・本番MLOps・LLM・drift検出保証は未対応。
---

# 固定推論教材への限定route

[README](../../README.md)の道筋、[UI](../../index.html)、[model](../../model.json)を読む。実行は既存[pipeline](../../pipeline.py)、[checker](../../verify.py)、[route](../../route.py)へ限定する。

module directoryで `python3 verify.py` はread-only。source/model/input digestを[receipt](../../observations/receipt.json)と照合して[raw](../../observations/raw.json)を引用する。原票更新を明示要求された場合だけ `python3 verify.py --record`。実IAB表示は既存 `python3 serve.py --port 0` のstartup URLを使い、自分のserver/tabを終了する。

正常routeは `python3 route.py schema`。inference/schema/feature-order/model-version/distribution-statistics/invalidが対応。`python3 route.py production-deploy` 等は未対応とし[coverage](../../coverage.json)を案内する。新serviceや依存の実装を対応済みと主張しない。作者routing smokeであり独立AgentEvalではない。

strictはnames/order/schema/model versionを計算前に検査。naiveは契約を意図的に無視する反例だが、値の有限性・長さ・0..100域検査は残す。交換した同意味入力でnaive=18.5、名前付き手計算=11。未知versionの出力は意味未定義で正答扱いしない。batch比較は記述統計のみで、検出保証、p値、精度低下、再学習判断ではない。

固定手動係数に学習性能の根拠はない。実ML訓練、LLM、本番serving、registry、CI/CD/CT、配信、課金、外部APIは未対応。[原典との対応](../../sources.json)と残る学習課題を示す。

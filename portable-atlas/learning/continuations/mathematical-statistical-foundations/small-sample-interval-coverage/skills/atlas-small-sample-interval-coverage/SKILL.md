---
name: atlas-small-sample-interval-coverage
description: n8 Bernoulliの保存Wald区間原票でnominal95%と理論coverageを区別し、独立256列Fraction oracleで検算する教材限定Skill。医療推奨・実データ精度保証には使わない。
---

[README](../../README.md)から予想→操作→比較→原典/実装/raw→答えを案内。[契約](../../contracts.json)と[原典](../../sources.json)を読む。通常[checker](../../checker.py)/route/閲覧はread-only、明示新採取の依頼だけ[runner](../../runner.py) --record。旧rawを上書きしない。

[route](../../route.py)はcoverage比較、k0の幅、k8の幅、外へ出る区間、単一観測の解釈、原票検算を扱う。3acceptedと7refusalを分け、nominal95%をfinite n coverageと同一視しない。z1.96は丸め指定値、clippingなし。256列全列挙をrandomsampling/実データ実験と呼ばない。1観測区間を真pについての95%posteriorへ置換しない。

医療の個別推奨、実データ精度保証、Wilson区間を計算、random samplingを実行は未対応と答え、READMEの未実験へ案内。元97入口/他単元/Goal/Portal/Node PID3901/port53478を変更せず、次実験を自動開始しない。

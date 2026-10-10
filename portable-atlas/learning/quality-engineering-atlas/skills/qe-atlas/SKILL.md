---
name: qe-atlas
description: QE Atlasの品質要求から測定・検証・統計・SLO・改善への入口とHTTP200/client timeout有限教材を案内する。
---

このdirectory内だけで `python3 -B verify.py` / `python3 -B route.py` を実行。模型を再計算し、保存実HTTP原票を読むチェックであり、実HTTP再実行と呼ばない。UIは自分の `python3 -B serve.py` のloopbackで予想→操作→正常/異常→source/raw→答えを案内し、所有tab/serverのみ終了する。

6request、3固定列、timeout1000/2000ms、window1500/2500msのみ。全発行requestの期限達成と受信responseのstatus率、server200試行を別分母で説明する。打切り観測待ちを真のlatencyへ代入しない。nearest-rank定義と少数例の限界を明示。予想/入力で旧raw/trace/答えを消し、予想を保持、旧保留結果を破棄する。

7章は入口。既存Requirements/SoftwareQuality/Math/SREを相対リンクで読む。Taguchi章のSN比/直交配列/確認実験は未実装。品質全体・母集団p95・実サービス安全性・理解度を保証しない。旧原票上書き、依存install、課金、権限/OS変更、公開/commit/push、Core gateは行わない。actual_http.pyの記録は明示新attemptだけで、使用済みattemptを再実行しない。

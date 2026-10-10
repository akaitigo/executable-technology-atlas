# Atlas — 原典と今回の規約

2026-10-07に [OpenTelemetry Metrics Data Model / Histogram](https://opentelemetry.io/docs/specs/otel/metrics/data-model/#histogram) と [Bucket inclusivity](https://opentelemetry.io/docs/specs/otel/metrics/data-model/#histogram-bucket-inclusivity) の公式本文を読みました。ページ表示は OTel 1.61.0。狭い参照範囲は Histogram の説明と bucket の上下端の段落です。

原典は histogram が測定値の集まりを圧縮して表すこと、区間件数と境界を持つことを説明しています。OTel の通常の明示境界では上端を含み下端を含まない規約があります。原典の sum・任意の min/max・時刻・temporality も含むデータモデル全体はここでは実装しません。

今回、渡す集約情報は有限の区切りと件数だけです。0〜40の有限領域、最初の区間の下端0を含む特例、q端点、線形補間式は [CONTRACT](CONTRACT.md) の教材独自規約です。OTel の実装検証、Prometheus の histogram_quantile、全製品の補間動作と一致するという主張はありません。原典から補間式を引用したものでもありません。

## 既存の前提へ戻る

- [基礎の計装](related.html?doc=base)：元 README の「未教材coverage」metrics行（35行）に latency 分布の問いがあります。
- [欠落・遅着と生データ分位点](related.html?doc=collector)：README 24行の nearest-rank、空集合 null が今回の前提です。
- [前教材の範囲](related.html?doc=coverage)：COVERAGE の分位点行（8行）に histogram bucket誤差・sketch・補間法比較が残ります。
- [前教材の実装](related.html?doc=model)：model.py の stats（9〜12行）は p50/p95 を整数順位から取り、補間しません。
- [前教材のSkill](related.html?doc=skill)：見えている値の条件付き分位点と未知の母集団を分ける順序を再利用します。

これらは固定 allowlist の本文 viewer で開けるようにします。既存ファイルを編集せず、読取時のSHA-256を記録します。公式リンクの画面操作を通信遮断下で確認した場合は、URLへの移動と本文取得を別に記録します。

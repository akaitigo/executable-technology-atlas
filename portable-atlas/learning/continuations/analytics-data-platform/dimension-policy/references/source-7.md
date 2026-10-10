# 注文時点の地域履歴を結ぶ

前提はLEFT JOIN、注文ID単位の粒度、NULLとゼロ。読む順番は `index.html` の予想→条件と注文位置→正常・異常→実装と生結果→答え。 [元教材の集計粒度](../../../subjects/analytics-data-platform/README.md) と [SQLのLEFT JOIN・行保持](../../../subjects/relational-database-sql/README.md) を先に読むと、履歴JOINによる増幅・欠落を区別できる。

## 固定する契約

架空の顧客c1の版1はnorth、[0,10)、版2はsouth、[10,20)。整数時刻0..20、版ID1..32一意、注文ID一意、金額は整数0..1000。o1はt9・100、o2はt10・50。実際のSQLite `:memory:` で `valid_from <= t AND t < valid_to` を評価しnorth100/south50を得る。latest故障例では最大valid_fromの属性へ結びsouth150。latestは故障を観察する比較条件で、当時の売上を表さない。

gapはt9の100をGAPへ、unknown-keyはo2の50をUNKNOWN_KEYへ残す。LEFT JOIN結果を注文IDで分類するため内結合による黙示的消失はない。overlapではo2が版1・2に一致しREFUSED_MULTIPLE_MATCH、集計null。無効区間はSQL前の入力拒否。absent_columnを問い合わせる意図的故障は実際のOperationalErrorをEXECUTION_FAILUREとして記録し、通常の答えを出さない。

## 再現する

```sh
python3 -B verify.py
python3 -B route.py
python3 -B serve.py
```

serveはこの教材と関連READMEの2本だけを一時loopback表示する。画面は保存データの説明でありSQLを再実行しない。21整数時刻の境界、10無効入力、6結果改変を独立台帳と照合する。`oracle.py` はSQLやproducerをimportせず、注文ID→版の固定表と手計算100+50を使う。実行記録の作成は明示的な未使用 `--record attempt-01` の一回のみ。通常checker/routeは書かない。

## 根拠と実用判断

[KimballのType 2解説](https://www.kimballgroup.com/2008/09/slowly-changing-dimensions-part-2/) は変更時に新しい行と代理キーを作り、有効開始・終了を管理して当時の属性を扱うことを説明する。本教材の整数時刻、有限終了20、半開区間SQL、異常分類は自分で定めた検証契約。履歴用キーをfactへ割り当てる本番パイプラインまでは実装しない。

地域別の当時売上ならas-of、現在の地域で再分類する目的ならlatestと指標の意味を明記する。間隙・未知キーは未分類金額を別に示す。重なりを勝手に一版へ丸めない。本番DWH、タイムゾーン、遅延訂正、分散ETL、性能は未検証。SubjectやAtlas全体の完了を意味しない。次は重なりの履歴全域検査、遅延到着の再処理、時刻型とタイムゾーンを個別に検証する。

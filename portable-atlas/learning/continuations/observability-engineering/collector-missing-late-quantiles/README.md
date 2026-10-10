# collector欠落・late arrivalと条件付き分位点

[教材](index.html)で予想→schedule/cutoff/閾値操作→collector観測と教学Oracle比較→source→答えを読みます。[既存QEの②](../../../quality-engineering-atlas/COVERAGE.md)に残っていたcollector欠落を独立pathで試す有限模型です。QE既存入口・原票は変更していません。

このdirectoryで既存Mac Python標準ライブラリを使います。

```sh
python3 -B verify.py
python3 -B route.py
python3 -B model.py
python3 -B serve.py
```

server表示の127.0.0.1動的URLを開きます。終了はそのprocessへCtrl+C。評価はmemory-onlyで、serverはsource/保存記録の読み取りと模型評価だけを提供します。UI再試験も通常verifyも原票を書きません。初回record/sealは制作時専用で既存の再記録は拒否します。file URLでAPIは使えません。install、実collector、外部通信の配送試験、公開、commit/push、Core/global gateは今回の範囲外です。

## 測定契約

独立した発行台帳にt=0発行r1..r6の6IDがあり、分母6を知れる仮定です。教学側の完全latencyは100,200,400,800,1800,2200ms。request完了時刻とcollector収集到着時刻は別です。全取得は全記録が2400msに到着。lateはr1..r4が2400、r5が4000、r6が5000msに到着します。

選択欠落は高latency r5/r6、低latency r1/r2、または全6件を永久に届けない合成scheduleです。永久欠落の確定は**4500msに明示最終loss noticeが届く**契約で、単なる無応答から推論しません。このnoticeは合成fixtureの確定通知であり、実pipelineが必ず同じ保証を持つとはしません。到着もnoticeもcutoffと同時なら含みます。

cutoffは1000/2400/4000/4500/5000、good閾値は400/800ms。到着済みはSEEN、最終notice済みはCONFIRMED_MISSING、それ以外はPENDINGです。未観測latencyと将来の到着/noticeはcollector viewではnull。確定欠落もrequestのlatency品質を確定しないため、good率の上限から除外しません。

seen統計は観測済みlatencyへの条件付き。平均はseenのnを分母とした正確なFraction、p50/p95は昇順 `x[ceil(p*n)-1]` のnearest-rank（補間なし）です。[既存QE契約](../../../quality-engineering-atlas/README.md)と接続します。偶数nのp50を中間2値の平均にしません。空はstats/seen率をnull（未定義）、0msや0%に置換しません。全台帳latencyの分布はcollector側では未推定のままです。

seen good率は既知good/seen。全発行good率は `[既知good/6, (既知good+未観測件数)/6]`。pendingと確定欠落のlatencyは両方未知です。未知を0やseen平均で補完せず、欠落そのものをrequest品質失敗と数えません。

| cutoff/schedule、閾値800ms | collectorの観測 | 教学側との比較 |
|---|---|---|
| 2400 全取得 | 6seen、平均2750/3、p50=400、p95=2200 | teachingと一致、good4/6 |
| 2400 late | 4seen/2pending、平均375、p50=200、p95=800 | seen good4/4、全発行範囲[2/3,1] |
| 4000 late | 5seen/1pending、平均660、p95=1800 | 全発行範囲[2/3,5/6] |
| 5000 late | 6seen/0pending、p95=2200 | 全取得と一致 |
| 4000→4500 高latency欠落 | 4seen/2pending→4seen/2確定欠落 | seen p95=800、全発行範囲は[2/3,1]のまま |
| 4500 低latency欠落 | 4seen/2確定欠落、平均1300、p50=800、p95=2200 | seen good2/4、全発行範囲[1/3,2/3] |
| 1000／全欠落 | empty seen統計は未定義 | 全発行範囲[0,1]。後のnoticeでもlatencyは未知 |

全latencyを知る教学Oracleを別panel/raw fieldへ表示し、seen−完全台帳の偏りを比べます。これは現実のcollectorが未知を知る主張でも欠測補正の推定結果でもありません。選択欠落の機構も教学fixtureだけが知っています。

## 根拠と検証

[Google SRE Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) のIndicatorsはSLI・観測窓と集計、Collectingは測定地点によって利用者問題を見逃すこと、Aggregationは平均で隠れる分布の裾を読む入口です。本fixtureのloss通知、bias、nearest-rankは独自の有限契約です。原典の一般論を実collectorの観測証拠に置き換えません。

実装前[手表](hand-oracle.json)を固定し、50条件、14schema拒否、8つの意味あるfaultを検査します。[独立Oracle](oracle.py)はmodelをimportせずliteral表とID/値/状態を照合します。制作中のscenario配列/object TypeErrorは旧sourceと失敗原票を保持して修正しました。[VERIFICATION.md](VERIFICATION.md)、[COVERAGE.md](COVERAGE.md)、[module Skill](skills/collector-quantiles/SKILL.md)を参照してください。

保存rawはsource viewerで先頭32768文字に限り、EXCERPTと総文字数・全文保存リンクを明示します。全文ファイルは変更しません。UTC/runtime/source SHA、CLI原票、実ブラウザcompact原票、capture保存可否、cleanupをobservationsに保持します。コード・図・文章は独自制作、Apache-2.0です。

---
name: atlas-finops-cost-engineering
description: 架空固定ratecard/usageのcent配賦・丸めgap・unallocatedを保存原票と独立Fraction oracleで案内する。実市場価格、billing操作、税計算、実財務助言には使わない。
---

# source centと配賦leafを検算する

教材rootはこのSkill Directoryから `../../`。[README](../../README.md)の道筋と架空範囲を読み、[UI](../../index.html)で予想→保存計算比較→raw cost tree→原典/実装→答えを案内する。今回の既存runner/checker/UIだけへrouteする。

- shared費用の丸めで総額は変わるか：equal-conserved / equal-naive / round-up-conserved / round-up-naive。共有10は4/3/3対3/3/3、共有11は4/4/3対4/4/4。gap+1/−1の意図異常を成功配賦と呼ばない。
- 余りは誰へ行くか：tie-reordered / one-cent / fractional-usage。floor後の残り、余り降順、同率team ID昇順のrecipientを [保存原票pointer](../../observation-data.js)で辿る。
- ownerが不明なら：missing-tag / no-basis。unallocated direct/sharedを保ち、丸めgapと分ける。gap0を全owner確定と呼ばない。
- 入力境界：zero-sharedは有効、zero-quantity / float-quantity / nonfinite-rate / duplicate-usage / zero-weightはcost treeなしで拒否。受入amountはdecimal文字列、context固定、binaryfloat経由の計算なし。
- 検算：教材rootで `PYTHONDONTWRITEBYTECODE=1 python3 checker.py`。[checker](../../checker.py)はread-only、Decimal/calculatorをimportせずFraction/整数と手計算を比較。[quick_validate](../../quick_validate.py)は限定routeの構造検査。
- 新原票の明示採取を依頼された場合だけ `PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record`。[runner](../../runner.py)で新runを作り、oracle成功時だけpointer更新。通常閲覧では原票更新しない。

画面は架空固定ratecard/usageであり、市場価格・実財務助言ではないことを示す。一時 `python3 -u -m http.server 0 --bind 127.0.0.1` の表示portでtitle/条件/tree/gap/raw/captureを確認し、owned serverを終了。bind/capture拒否は記録し、通常審査を使い禁止を迂回しない。

「実クラウド価格を取得」「billing APIで請求変更」「実税額を計算」「契約購入の財務判断」はこの教材では未対応と答え、[READMEの次実験E1–E4](../../README.md)と[公式locator](../../sources.json)へ案内する。pricing/billing API、外部service、新権限/設定、Core/Graph/Portal/Harness/Goalへrouteしない。単一架空currencyの保存条件を税/FX/provider規則や公平な配賦の証明へ拡張しない。曖昧な問いは境界を確認し、今回から判断できることを先に示す。

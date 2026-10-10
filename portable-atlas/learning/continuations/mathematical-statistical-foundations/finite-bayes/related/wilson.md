# Wilsonの端点は収まる。n=8で95%を覆う？

[既存Wald教材の次案1](../small-sample-interval-coverage/README.md)を、この専有directoryだけに実装します。旧source/raw/QA/Subject/Portalは変更しません。独立Bernoulli8回、教材の既知true p=.1/.5/.9、丸めz=1.96で、WaldとWilsonの9区間・包含・全256列のweighted coverageを比較します。中央受入待ちの有限unitです。

| true p | Wald covered k / coverage | Wilson covered k / coverage | Wilson−Wald |
|---|---|---|---|
| .1 | 1,2,3 / .56450844 | 0,1,2 / .96190821 | .39739977 |
| .5 | 2..6 / .9296875 | 2..6 / .9296875 | 0 |
| .9 | 5,6,7 / .56450844 | 6,7,8 / .96190821 | .39739977 |

これは[実装前literal手表](hand-oracle.json)です。[事前時刻・SHA](qa/oracle-before-producer.json)でproducer未作成時の固定を記録。p=.1のWilsonはmass .43046721+.38263752+.14880348、p=.5は(28+56+70+56+28)/256=119/128。p=.9は成功/失敗の対称性で同値。bounded endpointだけで95%coverageを保証しません。p=.5では両手法がnominal95%を下回ります。この3p/固定nではWilsonが劣らない観測でも、他条件への一般的優劣は未検証です。

## 予想 → 操作 → 2手法図/比較 → 原典/raw → 答え

[画面](index.html)で入力例・coverageの予想を選び「この実入力を計算して比較」。有限JSONを編集すると、実際にPython childへPOSTして再計算します。保存例の再表示だけではありません。Wald/Wilsonの全9区間図、教材true p破線、太い観測k、包含と二項mass、実計算JSON、独立oracleへのリンクを読み、答えを開きます。

入力例・予想・JSONを変更すると旧図/表/trace/答え/raw linkを空にし、開いたdetailsを閉じ、新値を保持。遅れて返った古い応答は表示しません。拒否exit2は区間/coverage/答えなし。childや通信失敗は別にし、正常答えを生成しません。previewの明示600ms遅延はstale-response確認用で、統計性能の測定ではありません。

```sh
python3 -B checker.py
python3 -B runner.py
python3 -B qa/check-ui.py
# 新原票を採取するときだけ
python3 -B runner.py --record
python3 -B server.py --record
```

既存Mac Python標準libだけ。serverは所有loopback動的port。表示URLを開き、終了時は所有serverのみCtrl-C。保護port53478/60285は操作しません。インストール/課金/公開/commit/pushなし。通常checker/runner/QAはunit全ファイルのSHA256/mtimeを維持。recordのみ新UTC原票を作成し、既存原票を上書きしません。source改稿後は明示recordと新preview originで再検証します。

## 2式と独立検算

[producer](calculate.py)はDecimal precision40/HALF_EVENで区間端点を計算し、9項 `C(8,k) p^k (1-p)^(8-k)` を加重します。p_hat=k/8。

Waldは `p_hat ± z sqrt(p_hat(1-p_hat)/8)`、clippingなし。k0/8で幅0、k1/7で[0,1]をはみ出す端点を保持。

Wilsonは `center=(p_hat+z²/16)/(1+z²/8)`、`half=z sqrt(p_hat(1-p_hat)/8+z²/256)/(1+z²/8)` のcenter±half。k0/8は式から導く厳密な境界0/1を指定し、浮動丸めをclippingで隠しません。k0区間[0,2401/7401]、k8[5000/7401,1]で幅は正です。その他端点と有理境界の小数表示は近似値です。

[独立checker](checker.py)はproducer/comb/sqrtをimportせず、全256列のFraction積からmassとcoverageを求めます。Wilson包含はscore testの平方不等式 `8(p-k/8)² <= (49/25)² p(1-p)`、Waldは右辺 `(49/25)²(k/8)(1-k/8)`。包含・mass・coverageはexact Fractionで照合。端点は二次式残差、和、幅、反射対称性、k0/8有理端点を1e-36許容で検算します。全3p×9観測kを通し、nominal偽保証/clipped Wald/WaldをWilsonと誤称/zero width/包含/mass/選択/拒否を成功扱いする8mutantを拒否します。

## 入力・解釈の境界

[契約](contracts.json)はexact keys n/p/z/k。nはboolでない整数8、pは文字列0.1/0.5/0.9、zは文字列1.96、kはboolでない整数0..8。NaN/Infinity、duplicate keys、未知field、float k、他n/p/zは拒否。任意パス/SQL/実データを受けません。

nominal95%は正規近似手続きの名前。z=1.96は丸めcritical値で、正確なnormal quantileではありません。全256列の理論集計をrandom sample・経験的coverage・実データ性能と呼びません。真p既知は包含を検算する教材条件であり、現実の推定で真pを知れるという意味ではありません。

観測kを固定した具体区間は真pを含むか含まないか。反復coverageは、標本を繰り返したとき区間手続きが真pを覆う確率。「この固定区間に真pが95%の確率で入る」というposterior解釈に置換しません。実データ、選択bias、依存、医療等の個別助言、他n/z/pは未評価。

[NIST §7.2.4.1](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)のFormulasと通常confidence expressionをWilson/Waldの式へ、Terminology NoteをWilsonとadjusted Waldの区別へ結びます。原文転載なし。[sources](sources.json)に日付/locator/binding。[COVERAGE](COVERAGE.md)は今回と未教材を分け、[有限Skill](skills/atlas-wilson-wald-finite-coverage/SKILL.md)は同じ範囲へ案内します。[QA](qa/README.md)に実IAB画像、編集/遅延/拒否/通信失敗、cleanup、失敗履歴とSHAを保存。全Subject/Atlas完成・formal delivery/fullGateは主張しません。

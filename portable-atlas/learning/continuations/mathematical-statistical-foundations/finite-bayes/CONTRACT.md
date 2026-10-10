# Atlas｜未知の割合を二つの仮説に絞って更新する

目標02と元学習経路§5／§6実験1に対応する有限模型です。前提は分数、条件付き確率、全確率。既知populationの割合から逆条件を求める既存教材を読み、今回は未知の表確率pについての仮説へ重みを付けます。Bayes式そのものを新しい知識として再制作するものではありません。

## 固定した意味と入力

仮説はHlow: p=1/4、Hhigh: p=3/4の二つだけ。どちらか一つのpが実験を通して共通で、**各仮説を条件としたとき**コイン結果は独立同分布と仮定します。仮説を混ぜた周辺分布で独立と主張しません。Hは表、Tは裏。現物coinを投げたり乱数で標本を生成したりしません。

関数への要求は `weights` と `observation` だけのdictです。weightsは順にHlow/Hhighの非負整数2個、各0..9、合計は正。bool・floatは整数扱いしません。仮説は入力で変更しません。

- 列観測：`{"type":"sequence","value":"HTT"}`。H/Tだけ、長さ0..3。空列は観測なしです。
- 個数観測：`{"type":"count","n":3,"k":1}`。整数0≤k≤n≤3。boolは拒否。各形式のkeyは上記だけです。
- 拒否順は要求shape→prior→観測。理由は `request-invalid`／`prior-invalid`／`observation-invalid`。拒否時payloadはnull。未知key・型・範囲を勝手に補正しません。

8正常入力と10拒否入力を[cases.json](cases.json)に固定しました。正常8件で全有効入力や全guard端点を網羅するわけではありません。pがどちらも0<p<1でprior合計が正のため、有効入力の観測確率は正です。分母0の実例はこの模型に作りません。

## 比較する計算

priorはweightsの合計で正規化。列sの尤度はp^k(1−p)^(n−k)、個数K=kの尤度はC(n,k)倍です。joint=prior×likelihood、evidence=jointの総和、posterior=joint/evidenceをFractionで保存します。

HTTと「3回中表1回」は別の事象です。後者はHTT/THT/TTHの3列を含むため尤度とevidenceは3倍ですが、今回のiid仮説では仮説に共通の係数が消えposteriorは一致します。この一致を任意の観測過程へ一般化しません。

主な手期待は尤度(9/64,3/64)、prior1:1ならposterior(3/4,1/4)、prior1:3なら(1/2,1/2)、prior1:9なら(1/4,3/4)。prior0:1なら低p側は0のままです。空列の尤度は(1,1)、posteriorはpriorです。詳細は[expected.json](expected.json)。

二つの誤った計算を同じ入力で対照します。①尤度をそのまま事後確率と呼ぶ（仮説間で和1とは限らない）、②尤度だけを正規化してpriorを無視する。②は等priorでは正しい結果と代数的に一致し、prior変更で差が出ます。この対照を別の推定手法として正当化しません。

## 独立照合と受入

producerはFractionのべきと組合せから計算します。独立担当は実装読取前の8列×2仮説のliteral mass表から観測の同時確率を集計し、8正常・10拒否を照合します。実行時入力/source、保存結果、期待値のhashを結合し、欠落・prior無視・事象係数欠落・拒否payloadなどのメモリ上の改変を拒否します。

実行は既存Mac Python stdlibのみ。rootと枠を確認し、fresh CPU/load/memory/既知処理、実nice10の設定と読戻し、逐次の子と各15秒の上限を守る短い1回です。現在計算0、GUI/browser/image0。画面は保存した計算結果のreaderとして準備し、実DOMと画像が未確認ならaccepted:falseを維持します。

予想→保存結果→事前・尤度・joint・正規化の対照→原典/実装→答え→限界の順で説明します。Skillの有限3例は、既知populationとの違い、列と個数の違い、prior0とモデル範囲外の判断です。

現実の率・priorの妥当性、連続posterior、Beta分布、confidence/credible interval、一般のsampling・欠測・選択bias、因果、医療判断、一般Agent評価は未対応。元repo/旧教材/共有台帳への変更・統合・加算は行いません。

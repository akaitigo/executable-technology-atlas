# Control systems / simulationを学ぶ道筋

この文書は[一次遅れと比例feedbackの既存教材](README.md)から、数値法、sampled controller、飽和と追加stateへ進むための補足です。有限教材の補足であり、制御分野全体の学習完了や実機性能・安全性を示しません。次実験は全て未実行です。

## 1. 前提と主要概念

差分・微分方程式、指数関数、feedback、平衡点、誤差、時系列を理解します。学ぶ順序は **plantとcontroller → 閉ループ平衡と定常偏差 → 連続時間解 → 数値更新と刻み幅 → sampled controller → 飽和・I/D項 → 遅延・noise・周波数応答 → 同定・状態推定・実機** です。

既存plantは `dy/dt=(-y+u)/tau`、`u=K(r-y)`、tau=r=1、初期y=0です。clipなしの平衡は `y*=K/(1+K)`。Eulerの更新係数 `a=1-h(1+K)` と連続時間の減衰率を区別します。K≥0のこの連続系は安定でも、選んだhで数値更新が発散し得ます。

目標へ近いこと、発散しないこと、過渡応答が速いこと、入力上限を守ることは別の評価軸です。clipで非線形になった系へ、飽和なしのaによる分類をそのまま移しません。

## 2. 予想から既存実測へ

[UI](index.html)、[simulator](simulator.py)、[5条件の全時系列](observations/presets.json)、[保存試験結果](observations/tests.json)、[QA](QA.md)を読みます。今回は計算・試験・UIを実行していません。

| 条件（K=2、40更新） | 保存済みa / 最終y | 予想を確かめる問い |
|---|---|---|
| h=0.1、clipなし | 0.7 / 0.6666662422 | なぜ目標1へ到達しないか |
| h=0.5、clipなし | −0.5 / 約2/3 | なぜ1、0.5、0.75…と振動するか |
| h=2/3、clipなし | −1 / 約0 | 最終値だけで減衰と判断できるか |
| h=0.8、clipなし | −1.4 / −466691.1311 | なぜ連続解が安定でも数値発散するか |
| h=0.1、入力上限±0.35 | 線形a=0.7 / 0.3448266910 | 要求uとclip後uの違いは何か |

5条件は各41点、CPython 3.9.6のCPU計算です。hで観察終端時刻が変わるため、40更新の値を同時刻比較にしません。clipなしは独立離散閉形式、常時上限clip条件は別の特殊解と照合済みです。一般clipには解析Oracle未適用を表示します。6保存試験の成功はこのモデルの計算検査に限ります。

既存QAの任意clip条件でも、線形aを非線形系の判定として扱いません。clip時の連続飽和なしの線は反実仮想です。既存UIはPythonを呼ぶ経路ですが、今回の文書では保存原票を読んだだけです。実機、HIL、リアルタイム制御の記録ではありません。

## 3. 実務で何を判断するか

方程式、単位、time constant、入力上限、観察時刻、solverとcontrollerの更新周期を明示します。gainを上げると定常偏差は小さくなっても、同じhのEulerが安定範囲を外れる場合があります。数値精度・離散controllerの安定性・実plantの安定性を別に調べます。

結果は全時系列、誤差、overshoot、入力要求、clip時間、適用できるOracleで判断します。I項が入れば蓄積state、飽和解除後の回復、anti-windupが追加の問いです。noise・delay・量子化・モデル誤差を省いた結果から実controllerの設定値を決定しません。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [MIT 18.086 Spring 2006, 8 Feb transcript](https://ocw.mit.edu/courses/18-086-mathematical-methods-for-engineers-ii-spring-2006/806b14f6a7a07a2209735c5162b567aa_gv-AB35V2k8.pdf)、PDF pp.9–11 | forward/backward Eulerと負の実固有値の安定境界 |
| [MIT 6.302 Spring 2007 Recitation 6](https://ocw.mit.edu/courses/6-302-feedback-systems-spring-2007/680f67691cfadcea9aa8a82e6f4c3654_6_302rec6.pdf)、PDF p.4、pp.5–6 | 比例gainの定常偏差、積分と定常誤差への入口 |

sample-and-hold、anti-windup、遅延の次実験は以下で定める独自modelです。上記資料がそれらの実装・実験を確認した証拠とはしません。

## 5. 未教材の問い

| 未教材 | 問いと次の入口 |
|---|---|
| solver比較・同時刻の誤差・厳密離散化 | 計算法の発散とsampled制御の挙動を分けられるか。実験1 |
| I項・windup・anti-windup | 飽和中に蓄積するstateが回復へどう影響するか。実験2 |
| 伝達遅延・sensor noise・量子化 | feedbackに入る値と実stateはどう違うか。実験3 |
| D項・filter・周波数応答・root locus | gain/phaseとnoise増幅をどう評価するか。別教材が必要 |
| state space・観測器・Kalman・MIMO | 見えないstateと多変数をどう扱うか。未実装 |
| plant同定・不確かさ・robust制御 | modelと現物の差をどう見積もるか。未測定 |
| 実機・HIL・リアルタイム・安全認証 | I/Oと締切・故障条件をどう検証するか。このCPU教材では未評価 |

## 6. 次の実験案（3本、全て未実行）

1. **同じ終端時刻で計算法とsampled controllerを比較する。** 独立fixtureでK=2、clipなし、T=4を固定し、h=0.1/0.2/0.8のforward/backward Eulerを連続閉ループ解へ照合します。各方法の独立漸化式をOracleにし、終端誤差と全時系列を比較します。さらに各sampleでuを決め区間内で保持する別modelを、plantの厳密更新 `y[n+1]=exp(-h)y[n]+(1-exp(-h))u[n]` で比較します。予想はsolverを変えた安定性と、held-input controllerの安定性が同じ問いではないことです。原典は18.086で、保持入力式は独自導出です。精度向上を実機安定性へ拡張しません。

2. **PIの蓄積stateと飽和解除を比較する。** 独自fixtureで `u_requested=Kp*e+Ki*z`、`z[n+1]=z[n]+h*e[n]` を先に定義し、同じ旧stateからyとzを更新します。飽和なし、飽和あり、外向き飽和時に積分を止める条件付き積分を比較します。固定reference列を高い目標から低い目標へ切り替え、z、要求/実u、overshoot、整定判定を保存し、Ki=0のP対照と初期数stepの手計算へ照合します。予想は飽和中の蓄積が回復を遅らせ得ることです。6.302の積分は概念入口であり、anti-windup規則は独自案です。solver誤差も確認し、PID全機能・安全性の保証にはしません。

3. **delayとnoiseを一因子ずつ比較する。** 独立の小刻みfixtureでfeedbackを現在yと1sample前yで比較し、初期historyの値を固定します。別条件で手書きの有限noise列を測定値だけへ加え、さらに独自量子化規則の有無を比べます。予想は真のyとcontrollerが見た値が違い、要求uや誤差の時系列が変わることです。noiseなし・delayなし対照、初期stepの手計算、刻み幅変更を照合し、noiseを乱数分布や実sensor測定にしません。feedbackと誤差を読む6.302を入口とする独自modelで、遅延系一般の安定性・確率保証・周波数全域評価は未実証です。

## 7. 資料取得と検証状況

2026-10-05に上記MIT 2 PDF本文を取得し、参照箇所を確認しました。今回の2資料は取得成功です。[既存QA](QA.md)にある大きなPDFのサイズ制限、Caltech timeout、Michigan CTMS 403は過去の未確認状態として保持し、今回再試行していません。第三者本文・図は保存していません。

追加はこの文書だけです。simulator、試験、server、UI、実機、global gateを実行せず、旧原票・画像・QA・digestを更新していません。次実験の予想は新たな計算実測ではありません。

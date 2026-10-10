# 一次遅れと比例feedbackを観察する

標準PythonのCPUシミュレータで、gain・刻み幅・入力飽和を比較する1教材です。実機の制御器、リアルタイム計測、HILではありません。Portalや旧Argo CDの完成Gateとは独立した有限の教材です。

## 開く・再計算する

このmoduleディレクトリで実行します。Python 3.9以上、追加packageなし。今回の実行版はCPython 3.9.6 / Darwin arm64です。3.9は既にサポート終了版のため、新規環境では保守中のPythonを使用してください（その版での追試は未確認）。

```sh
python3 -m unittest -v test_simulator
python3 simulator.py --record
python3 serve.py
```

`http://127.0.0.1:18771/` を開きます。ローカル専用、外部公開なし。終了はserverのターミナルでCtrl-C。`--record`は5条件の入力・全時系列・実行版・UTC時刻・command・実装SHA256を`observations/presets.json`へ保存し、同じJSONをstdoutに出します。再実行するとこのCLI原票は置換されるため、旧結果が必要なら実行前に別名で保管してください。UIの各runは固有名`observations/ui-*.json`へ保存します。未実行結果は事前作成しません。

## 学び方

1. 固定正常条件を見る。K=2、h=0.1、clipなし。yは目標1ではなく約2/3へ近づくと予測できるか。
2. 「減衰振動」を選択。予測を選び「Pythonで計算」。yは1、0.5、0.75…と振動して近づく。
3. 「安定境界」「発散」へ変える。aの絶対値と波形の対応を見る。
4. 「入力飽和」を選択。uの要求値と実際のclip値を比較する。
5. 式、実装、今回の生JSONを見て答え合わせ。K=12、h=0.2とh=0.05でも試す。

## モデル・Oracleの区別

plantは `dy/dt=(-y+u)/tau`、`u=K(r-y)`、tau=r=1、y0=0。実装は現在のyから傾きを計算するforward Eulerであり、Oracleの値をそのまま実行結果にしません。

clipなしでは `a=1-h(1+K)`、`y*=K/(1+K)`、離散解 `y[n]=y*(1-a**n)`。この解と各時点のPython結果を、`abs(actual-expected)/max(1,abs(expected)) <= 1e-12`で照合します。K≥0の連続時間解析解 `y(t)=y*(1-exp(-(1+K)t))` は安定ですが、Euler更新は|a|>1で数値発散します。これを物理plantの不安定性と同一視しません。

常時上限に達するclip条件（h≤1かつK(1−Umax)≥Umax）では独立の特殊解 `y[n]=Umax*(1-(1-h)**n)`を使います。それ以外のclip条件は解析Oracle未適用と表示します。線形aの分類はclipした非線形系全体の安定性判定ではありません。

5 presetは40更新、各41点。hによって観察時間が違います。各plotは独立の軸、発散時の尺度も明示しています。橙線は連続時間・飽和なしの解なので、clip時は反実仮想です。

## 実観測（2026-10-05 UTC）

原票：[presets.json](observations/presets.json)。ブラウザ操作と画面：[QA.md](QA.md)。

| 条件 | K | h | clip | a（線形Euler） | 40更新後y |
|---|---:|---:|---:|---:|---:|
| 安定 | 2 | 0.1 | なし | 0.7 | 0.6666662422 |
| 減衰振動 | 2 | 0.5 | なし | −0.5 | 約0.6666666667 |
| 安定境界 | 2 | 2/3 | なし | −1 | 約0（丸め誤差あり） |
| 発散 | 2 | 0.8 | なし | −1.4 | 約−466,691 |
| 飽和 | 2 | 0.1 | ±0.35 | 0.7（clip系の判定ではない） | 0.3448266910 |

6 unit検査：5 presetの全時点Oracle、挙動と先頭値、連続解へ刻み幅半減で誤差縮小、gain/刻み幅の組合せ、一般clipの非過大主張、不正入力拒否。全て成功。これらはこのモデルの計算検査であり、PIDの全面検証ではありません。

## 一次資料・版

- [MIT 18.086, Spring 2006, 8 Feb lecture transcript](https://ocw.mit.edu/courses/18-086-mathematical-methods-for-engineers-ii-spring-2006/806b14f6a7a07a2209735c5162b567aa_gv-AB35V2k8.pdf)、PDF pp.9–10：forward Eulerの更新係数と負の実固有値の安定境界。2026-10-05閲覧。
- [MIT 6.302, Spring 2007, Recitation 6: Steady-State Errors](https://ocw.mit.edu/courses/6-302-feedback-systems-spring-2007/680f67691cfadcea9aa8a82e6f4c3654_6_302rec6.pdf)、PDF p.4：一次遅れと比例gainでstepの定常偏差1/(1+K)。2026-10-05閲覧。
- [Python 3.9 math.exp](https://docs.python.org/3.9/library/math.html#math.exp)、参照時表示版3.9.25：指数関数。実行interpreter3.9.6とはpatch版が異なる。2026-10-05閲覧。

資料本文・図は複製していません。本教材の式・block図は選択したモデルから独自に構成した説明です。Caltech book・Michigan CTMSも検索しましたが取得timeout/403のため本文確認済み根拠にはしていません。

## 未教授・境界

PIDのI/D項、anti-windup、sample-and-holdの厳密離散化、伝達遅延、sensor noise、量子化、周波数応答、状態推定、MIMO、plant同定、実機接続、HIL、安全認証は未教授。教材のgainを実機へ適用しないでください。飽和は単なる数学的clipで、安全装置を表現するものではありません。

再利用入口：[atlas-control-systems-simulation](skills/atlas-control-systems-simulation/SKILL.md)。このmoduleのみのSkillで、global installや全Subject Skill完成を意味しません。

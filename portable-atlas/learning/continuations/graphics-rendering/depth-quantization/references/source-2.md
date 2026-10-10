# 三角形のcoverageとpixelごとの奥行き

標準Pythonだけで2面を16×12 pixelへ描き、depth testとdraw-order-only方式を比較する一教材です。各pixelの所属・正確depth・edge値・barycentric重み・採用/拒否を原票に保存し、Browserでは実PNGを拡大・decodeしてsampleできます。Subject全体の完成ではありません。

## 起動・検査

このdirectoryで実行します。追加パッケージ、GPU、外部サービスは不要です。

```sh
python3 -B verify.py
python3 -B verify.py --check observations/cpu-attempt-01/run.json
node audit.mjs
node serve.mjs
```

serverが表示する動的loopback URLを開きます。終了はCtrl+C。他担当のport/processは停止しません。通常checkerはread-only。新しいCPU原票を求める場合だけ、未使用名を指定します。既存directoryがあれば拒否します。

```sh
python3 -B verify.py --record cpu-attempt-02
```

このUIは固定の検証済み `cpu-attempt-01` を表示します。新規原票を自動で成功扱いしたりUIへ差し替えたりはしません。独立照合は `--check observations/新規名/run.json` を指定できます。`node audit.mjs --record 未使用名` は監査の新規記録だけを保存します。

## 体験する

1. 描画順を逆にするとどうなるか予想する。
2. normal-abとnormal-baを切り替える。正常は同じ、painterは違う。
3. (7,5)を見る。normal-abではdepthがA=37/80を選ぶが、painterは奥のB=215/428を上書きしてしまう。
4. degenerate、grid外、shared-edge、winding、equal-depthを切り替える。共有辺の(5,5)は片面のみ。等しいdepthは先勝ちなので順序に依存する。
5. 各pixelの原票、Python実装、一次資料を読み、修正方針を回答する。

入力は整数x=0–15/y=0–11。範囲外、非整数、空欄は拒否します。CPU入力contractは座標整数-32..32、depthは0..1の有理数文字列、gridは1..32。現在の教材では2面・16×12だけを使用しています。

## 規則と根拠

pixel中心(x+½,y+½)、y下向き。正の面積へ頂点順を正規化し、辺上は上向きの辺または右向き水平辺を含むtop-left規則。depthはscreen-linearな有理数で小さい方を採用し、同値は先勝ち。viewport内のsampleだけを検査し、homogeneous clippingはしません。

[Microsoft Rasterization Rules / Triangle Rasterization Rules (Without Multisampling)](https://learn.microsoft.com/en-us/windows/win32/direct3d11/d3d10-graphics-programming-guide-rasterizer-stage-rules#triangle-rasterization-rules-without-multisampling) のpixel中心・共有辺規則と、[Depth Buffers](https://learn.microsoft.com/en-us/windows/win32/direct3d9/depth-buffers) のdepth保存/比較を参照しました。コード・素材は独自実装で、第三者のコード/画像を複製していません。

独立oracleは面積分割による包含判定と平面方程式でzを求めます。rendererのedge/barycentric関数は再利用しません。ただしtie規則は共通の契約です。GPU conformance、透視投影、有限精度、MSAA、照明の保証ではありません。[scope.json](scope.json) と [VERIFICATION.md](VERIFICATION.md) に未制作・未測定を分離しています。

[module-local Skill](skills/atlas-graphics-rendering/SKILL.md) はこのrunner/checker/UIだけに案内します。global installや公開は行いません。

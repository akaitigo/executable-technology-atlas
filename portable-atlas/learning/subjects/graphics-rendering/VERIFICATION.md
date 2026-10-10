# CPU raster教材の検証記録

## 問い・実行経路

交差する2面の手前は、固定の描画順だけで決められるか。pixel中心のcoverage、barycentric depth、depth testの違いを実演算と実画像で比較する一教材です。Subject全体の完成ではありません。

Python `raster.py` → 16×12のRGB PNG/全pixel原票 → task-owned loopback server → 背景IAB → PNG decode/sample、という経路を確認しました。BrowserはCPU rendererの代替計算をせず、PNGを拡大表示し、そのdecoded pixelを原票へ照合します。

## 実環境と日時

- CPU: CPython 3.9.6 / Darwin / arm64。2026-10-05 14:19:32.634910–14:19:33.074869 JST。原票はUTCで保持。
- Browser: IAB。UAはChrome/154.0.0.0、言語ja、viewport 1280×720。観測19状態は14:21:34.065–14:21:37.478 JST。UAのMac OS X 10_15_7を実OS版と断定しません。
- Node監査: v25.2.1 / darwin / arm64。
- 初回QAでtitle「pixelごとに奥行きを決める | CPU Raster Lab」とscene/x/y/sample fieldを確認。port0による動的port60557を使用。他担当listenerと取り違えていません。

## 規則を固定する

screen-space、x右/y下。pixel中心は(x+½,y+½)。頂点順を正のsigned areaへ正規化。辺上は上向き辺(dy<0)または右向き水平辺(dy=0,dx>0)を含め、他は含めないtop-left契約です。

zはscreen-linearな有理数、0..1、小さい方が手前。初期∞はJSON nullで表す。strict LESSなので同値は先に描いた面を保持する。面積0は描画しない。grid内のsampleのみを走査し、world/clip変換やhomogeneous clippingはしない。座標の制約外入力はclampせず拒否します。

一次資料locator: [Microsoft Rasterization Rules §Triangle Rasterization Rules (Without Multisampling)](https://learn.microsoft.com/en-us/windows/win32/direct3d11/d3d10-graphics-programming-guide-rasterizer-stage-rules#triangle-rasterization-rules-without-multisampling) のpixel中心/共有辺の説明と、[Depth Buffers](https://learn.microsoft.com/en-us/windows/win32/direct3d9/depth-buffers) の初期depth・比較/保存の説明を参照（2026-10-05確認）。コード・PNG・デザインは独自実装です。API全体の互換/適合やGPU実数値挙動は主張しません。

## CPU実演算と独立oracle

[CPU原票](observations/cpu-attempt-01/run.json) は入力頂点と順序、全pixelの所属・正確depth・浮動表示値・RGB・各面のedge/weight/採用/拒否を保存しています。10入力×2方式×192 pixel＝3,840件を検査しました。

rendererはedge関数とbarycentric重みを使用。独立oracleは面積分割の包含判定と、3頂点から解いた平面方程式でdepthを求めます。rendererのedge/weight関数を呼びません。辺上のtie規則は共有契約なので、その定義自体の独立仕様証明ではありません。

| 入力 | 実演算の結果 |
|---|---|
| normal-ab / normal-ba | depthは全pixelの所属/depthが同じ。painterは順序で変わり、depthとの所属差は10 / 9 pixel |
| degenerate | 面積0のAを拒否。Bの描画は継続 |
| partial-outside | viewport内だけを評価し、oracleに一致 |
| all-outside | 192 pixelすべて背景/depth未設定 |
| shared-ab / shared-ba | 6×6の36 pixelが穴/二重所属なく描画。順序によらず一致 |
| winding-reversed | Aの頂点順反転後もnormalのdepth出力と一致 |
| equal-ab / equal-ba | 同depth重なりは先勝ちで順序依存。depthの順序不変を誤って一般化しない |

正常・境界の8不変条件を確認。grid0/bool/33、NaN depth、契約外座標の5不正入力も拒否しました。20 PNGは再演算からの再エンコードbytesのhashとも一致します。

## 実IAB QAと負例

[Browser原票](observations/browser-attempt-01/browser.json) は入力操作、時刻、DOM snapshot、実環境、CPU原票hash/source binding、画像URL、sample結果を保持します。

10ケースを全て切替え(7,5)をsample。共有辺(5,5)、最後のpixel(15,11)、範囲外x/y・非整数・空欄の4拒否、回答3候補まで、19状態359照合が成功しました。[監査原票](observations/audit-attempt-01/audit.json)で保存記録を照合しています。この数は観測fixtureの照合数でありBrowserの全pixel網羅試験数ではありません。

normal-abの(7,5)はdepthがA=37/80、painterがB=215/428。Python RGB / Browser decoded RGBAはそれぞれ[22,118,124]/[22,118,124,255]と[224,123,45]/[224,123,45,255]で一致。shared-edge(5,5)はAのみcovered。raw断片をUIの展開表示でも確認しました。

監査は改変decoded RGB、stale CPU原票hash、別ケースPNG URLの3負例を拒否します。CPU/Browserの記録照合はfresh Browser runではない点を区別します。

## checkerとSkill

- `python3 verify.py`（-Bなしも含む）、`python3 -B verify.py --check observations/cpu-attempt-01/run.json`、`node audit.mjs` はexit0。前後の教材全ファイルhash集合が不変。通常checkerはpycacheも含めてread-onlyでした。
- `--record cpu-attempt-01` の意図的な再指定はFileExistsErrorで拒否し、成功原票/PNGの全hashが不変でした。既存記録を再固定・上書きしていません。
- `node --check lesson.js` / `serve.mjs` はpass。
- module-local Skillのquick_validateはpass。[同一Agent routing control](observations/skill-control.json)は通常ルートで既存shared-edge UIを操作し、GPU/clip/物理照明保証の対象外ルートを確認。独立Forward Evalではありません。

## hashと画面

全てSHA-256。全7 sourceと20 PNGのhashはCPU原票、監査器自身と主要Artifactのhash/byte数は監査原票にあります。

| ファイル | SHA-256 |
|---|---|
| raster.py | 597bb0ba1cc0d3ac1eef0791248f09b788319a7ca2a9010952466f3547cba437 |
| verify.py | f77ee032de951b4457b892f97ce1142f6420b1d300d66721c27b1dd43f17c45b |
| scenes.json | e471da6f2a1a0326c3c813e4e64ad8d29c8e21af65dd5dea2d0873b779b97e84 |
| CPU原票 / 4,745,509 bytes | 331bc0a0c474a890cd48ca7845eb01fce5bf19b65244444dc8ab958e9cc3993a |
| Browser原票 / 181,034 bytes | 79e5e909fe934df11aed8def37c264d2f7d7ee0f5b376285d747c13ca7d28cd7 |
| comparison-detail.jpg / 50,652 bytes | 2da98e20b426b8d94e809f583250bfa0232b3b5f226ff121fe115d8ec354829c |
| 監査原票 | c0e0208c427dfdc83178b567886b0b41fcad2e583ee84de7b28d71c605ee3083 |
| Skill control | 5c28136fc8db78a60374cf264eadc3ed6c69cfc2dd6aebbb594cbcdf456ca3a9 |

CPU PNGはRGB 16×12。IAB screenshotはJPEG 1280×720、無加工。最初のcomparison.jpgは画像下部がviewport外なので保持したまま、scroll後のcomparison-detail.jpgも保存しました。画像単独で実演算やsample一致を証明せず、原票と併読します。

![実CPU出力のBrowser表示](observations/browser-attempt-01/comparison-detail.jpg)

## 失敗保持・資源・未達

[運用記録](observations/operational-failures.json)にはread-only JSON確認用の一行PythonのSyntaxErrorと、意図的な原票上書き拒否を保持。前者は補助inspectionの失敗で、rendererやCPU記録生成の失敗ではありません。後者は期待どおりの拒否です。既存成功・失敗を削除していません。

自作IABタブをclose。own server sessionはCtrl+C/exit130で終了し、port60557のlistenerなしを確認しました。他タブ、共有Chrome、Cloudflare、他担当process、Docker、OS/GitHub設定、依存、global Skillは操作なし。旧repo、Portal root文書、Core/Graph、Goal、commit/push/公開も変更なし。

実GPU、shader/driver、透視投影、完全clip規則、照明、色管理、有限精度/MSAA、性能、全Browser組合せは未検証。高速連続切替のstress試験も未実施です。未教材領域は[scope.json](scope.json)に整理し、全Subjectの網羅性/完成は宣言しません。

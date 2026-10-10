# Graphics / renderingを学ぶ道筋

この文書は[三角形coverageとdepthの既存教材](README.md)から、座標変換、補間、有限精度、samplingへ進むための補足です。有限教材の補足であり、描画分野全体の学習完了を示しません。次実験は全て未実行です。

## 1. 前提と仕組み

座標、signed area、内積・行列、barycentric重み、有理数、pixelとsampleを理解します。学ぶ順序は **座標とcoverage → 共有辺と退化 → 属性補間 → depth比較 → model/view/projection・clip → 透視補間 → 精度とsampling → shading・texture・色 → GPU資源と性能** です。

coverageは「sampleが面に属するか」、depth testは「覆う面のどれを残すか」です。draw-order-onlyは後の面で上書きするため、交差面の手前をpixelごとに選べません。共有辺の包含規則、同depthのtie規則、頂点順の正規化も別の契約です。

既存の規約はx右/y下、pixel中心(x+1/2,y+1/2)、正の面積、top-left、screen-linearな有理数z、小さいzが手前、strict LESSです。viewport内sampleだけを評価することをhomogeneous clippingと呼びません。screen-space depthの補間を、texture UVの透視補間へ無条件に流用しません。

## 2. 予想から既存実測へ

[UI](index.html)、[renderer](raster.py)、[scene入力](scenes.json)、[CPU原票](observations/cpu-attempt-01/run.json)、[Browser原票](observations/browser-attempt-01/browser.json)、[監査原票](observations/audit-attempt-01/audit.json)、[検証記録](VERIFICATION.md)を読みます。今回は計算・checker・Browserを再実行していません。

| 条件 | 保存済み結果 | 何を説明するか |
|---|---|---|
| normal-ab / normal-ba | depth所属・zは同じ、painterは異なる | 順序で手前を決める予想の反例 |
| normal-abの(7,5) | depth A=37/80、painter B=215/428 | pixelごとの深さ比較 |
| shared-ab / shared-ba | 6×6の36pixelに穴・二重所属なし、(5,5)はAのみ | 共有辺の一方だけを含める規則 |
| winding-reversed | normalのdepth出力と一致 | 正の面積へ正規化する効果 |
| degenerate / all-outside | 面積0のAを拒否 / 全192pixelが背景 | 退化とviewport外の境界 |
| equal-ab / equal-ba | 先勝ちで描画順に依存 | depthなら常に順序不変、とはしない |
| 不正入力 | CPU5入力、UI4入力の拒否記録 | contract外をclampで成功扱いしない |

CPython 3.9.6による10入力×2方式×192pixel=3840照合です。独立Oracleは面積分割と平面方程式で、rendererのedge/barycentric関数を再利用しません。ただし共有辺tieの仕様は共通契約です。20 PNGはCPU出力、BrowserはPNGをdecodeしてsampleする経路です。19状態359照合はBrowser全pixelの網羅試験ではありません。

depth一致、画像hash一致、実画像の目視は違う確認です。GPU、shader/driver、浮動小数点、透視投影、MSAA、色管理、照明、性能の実測へ拡張しません。

## 3. 実務で何を判断するか

まず座標系、w、clip領域、sample位置、補間する属性、depth形式・比較・clear値を固定します。穴や二重所属、順序依存、z-fighting、UV歪み、aliasingは原因を分けて調べます。PNGに差があっても、どのsample・属性・数値契約が違うかを追える原票が必要です。

実APIへ移す場合はAPI版・driver・precision・sample layoutを記録し、CPUの有理数結果と照合する許容差を定めます。透過の合成順、線形光と表示用色、texture filteringはdepthによる可視面選択とは別の段階です。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [Microsoft Rasterization Rules](https://learn.microsoft.com/en-us/windows/win32/direct3d11/d3d10-graphics-programming-guide-rasterizer-stage-rules)、Triangle Rasterization Rules / Multisample Anti-Aliasing Rasterization Rules | pixel中心、共有辺、複数sampleとcoverage |
| [Microsoft Depth Buffers, Direct3D 9](https://learn.microsoft.com/en-us/windows/win32/direct3d9/depth-buffers) | depth保存・比較の概念 |
| [Microsoft Rasterizer Stage](https://learn.microsoft.com/en-us/windows/win32/direct3d11/d3d10-graphics-programming-guide-rasterizer-stage) | clip-spaceからviewportへの段階 |
| [Microsoft HLSL Struct Type](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-struct)、Interpolation Modifiers Introduced in Shader Model 4 | linear / noperspective / sample等の役割 |

これらは原理の入口です。以下の有限CPU案をDirect3D conformance試験と呼びません。

## 5. 未教材と次の問い

| 未教材 | 問いと次の入口 |
|---|---|
| model/view/projection・homogeneous clip・culling | divide前の境界をどう扱うか。実験1、変換行列とculling全体は別途 |
| perspective correction・UV | 同じscreen重みで属性を足してよいか。実験2 |
| depth量子化・有限精度 | 厳密に異なるzが保存形式で同値にならないか。実験3 |
| MSAA・coverageとshading | sampleを増やして何が改善し、何が残るか。実験4 |
| texture/filtering/mipmap・sRGB/HDR・alpha | 色とsamplingと合成の契約は何か。別教材が必要 |
| lighting/BRDF/PBR・shadow・ray/path/BVH | 光と可視性をどうmodel化するか。未実装 |
| animation・scene/asset・LOD・streaming | 時間変化と資源寿命をどう扱うか。未実装 |
| GPU API/shader/synchronization・profiling・回帰/互換性 | 実機でどの契約と性能を満たすか。実GPU未検証 |

既存の未制作一覧は[scope.json](scope.json)を保持します。この表も分野全体の網羅宣言ではありません。

## 6. 次の実験案（4本、全て未実行）

1. **divide前のclipを比較する。** 独立fixtureでclip座標(x,y,z,w)、w>0、−w≤x,y≤w、0≤z≤wという規約を明示します。近面を跨ぐ合成三角形を、clipせずdivideする故障版と、平面交点を有理数で求めpolygonを再三角形化する版で比較します。予想は頂点を捨てるだけでは境界の面を正しく保てないことです。手書き交点・内側判定・面積をOracleにします。Rasterizer Stageが概念入口で、w≤0や全退化・API全clip規則は別の未完条件です。

2. **UVの透視補間をscreen-linearと比較する。** 正の異なるwと固定UVを持つ合成面で、screen重みλによるΣλuと、独自導出の `(Σλu/w)/(Σλ/w)` を比較します。同wの対照と、射影前の幾何から別計算した手書きsampleをOracleにします。予想は異なるwで値が違い、同wでは一致することです。HLSL interpolation modifierは概念入口です。既存zをこの式で一律に補正する案ではなく、texture filtering・実shaderは未実行です。

3. **depth量子化とtieを比較する。** 独立fixtureで厳密有理数zと、独自のb-bit整数化 `floor(z*(2^b−1)+1/2)` を比較します。近い2値を同じbinへ入れる条件、異なるbinの条件、描画順反転を手書きbin表と照合します。予想は厳密な前後関係が量子化でtieになり、strict LESSの先勝ちが現れることです。Depth Buffersが概念入口で、実depth format、透視depth分布、reversed-Z、driver挙動の保証ではありません。

4. **単一sampleと固定4sampleのcoverageを比較する。** 独立fixtureで中心1点と各pixelの1/4・3/4位置4点を使い、同じ合成斜辺を走査します。各sampleにcoverage/depthを持ち、固定面色の算術平均をresolve規則として明示します。手書きmaskと独立面積包含Oracleへ照合します。予想は境界pixelに部分coverageが現れることです。Rasterization RulesのMSAAが入口ですが、独自sample layoutです。texture aliasing、sample shading、色空間、実hardware quality levelを測った扱いにはしません。

## 7. 資料取得と検証状況

2026-10-05に上記Microsoft 4ページの本文を取得しました。ページ内にauthorization案内はありますが、参照本文は取得できています。今回本文取得不能のURLはありません。第三者本文・画像・code exampleは保存していません。

追加はこの文書だけです。renderer、checker、GPU、server、Browser、global gateを実行せず、旧原票・画像・検証記録・digestを更新していません。次実験の予想は新たな描画実測ではありません。

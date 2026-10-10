# UVの透視補間を幾何と画像で確認する

前提: 座標、射影divide、barycentric重み、有理数。[既存coverage/depth教材](../../../subjects/graphics-rendering/README.md)と[学習経路の実験2](../../../subjects/graphics-rendering/LEARNING_PATH.md)から、属性補間へ進む有限続編です。Python標準ライブラリだけで動きます。

1. 同じscreen三角形でwを変えたとき、screen-linear UVが正しいか予想する。
2. `python3 verify.py`で保存済み実行を独立oracleと照合する。`python3 serve.py`が表示するURLで[UI](index.html)を開く。
3. 同w／異wを選び、基準sampleとpixel中心sampleを比較する。screen重み、1/wを掛けた重み、正規化後の重み、UV、生成PNGと差分を追う。
4. 範囲外入力の拒否、面外の正常な背景を区別する。原典locatorを読み、答えと実務判断を説明する。

主要概念: screen vertices=(0,0),(1,0),(0,1)、w=(1,2,2)、UV=(0,0),(1,0),(1,1)。screen点(1/4,1/4)のλ=(1/2,1/4,1/4)。直線補間ではUV=(1/2,1/4)、透視補正 `(ΣλUV/w)/(Σλ/w)` では(1/3,1/6)。同w=(1,1,1)の対照では両者一致する。

独立期待値は補正式の再実装ではない。camera vertices=(0,0,1),(2,0,2),(0,2,2)の平面z=1+(x+y)/2にray=t(1/4,1/4,1)を交差させるとt=4/3。交点(1/3,1/3,4/3)を元の三角形に展開したworld重み=(2/3,1/6,1/6)からUVを求める。[手書き事前例](hand-oracle.json)、[独立oracle/checker](verify.py)、[producer](raster.py)、[fixture](fixtures.json)、[raw](observations/attempt-01/raw.json)をつなぐ。

実務判断: coverageで用いたscreen重みをUVへそのまま流用すると、異wの面で歪む。既存screen-space depthを一律に同じ式で補正する主張ではない。どの座標空間の属性を、どの補間契約で渡すか固定する。[Microsoft HLSL Struct Type / Interpolation Modifiers](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-struct#interpolation-modifiers-introduced-in-shader-model-4)のnoperspectiveは透視補正を行わないmodifier。linearが既定という説明はAPIの語彙であり、このCPU画像をshader試験と呼ばない。

画像規約: 16×16、正規化viewport、pixel中心((x+1/2)/16,(y+1/2)/16)、y下向き、単一三角形の全辺を閉じて含める。共有辺top-left規約は対象外。R=round(255u)、G=round(255v)、Bは8×8 UV格子の偶奇で40/220。これは属性を見える色にする独自の符号化でありtexture filteringではない。背景RGB=(18,28,44)、差分はRGB成分の絶対差。PNGはRGB8/filter0、独立decoderでCRCと全画素を照合する。

入力契約: screen3頂点、正のw3値、UV3組の各成分0..1、非退化、有限有理数。UI pixelは整数0..15、基準点は別ボタン。viewport内の面外点は正常な背景、範囲外・bool・非有限・w≤0・退化などは拒否する。正のwだけの模型でありclipやclampで拒否を成功扱いしない。

限界: 実GPU・実shader・homogeneous clip・w≤0・任意renderer・filtering・色管理・precision保証は未検証。全Subjectの網羅ではない。原典は[source locator](sources.json)、未教材領域と次の3実験は[coverage](coverage.json)、結果は[検証記録](VERIFICATION.md)、案内は[module Skill](skills/atlas-perspective-correct-interpolation/SKILL.md)。答え合わせ: 異wではscreen重みとcamera重みが違う。同w対照と独立ray交点が、補正の必要な条件を分離する。

初回記録は`python3 verify.py --record attempt-01`。未使用名だけを許し、既存rawを上書きしない。通常checker/UIは固定attempt-01を読む。`--seal-record`はrawとPNGを変えずQA/source receiptを更新する。通常route/checkerはread-only。

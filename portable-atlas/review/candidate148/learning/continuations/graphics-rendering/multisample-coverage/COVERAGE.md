# Atlas — 複数のsample位置で補う範囲

177受入（既存127＋独立50）の入口と学習経路を基準に、目標91の「座標・精度・samplingの条件を選べる」という到達点へ進みます。共有 `graphics-rendering/LEARNING_PATH.md:7` は「精度とsampling」を前提順に置き、同`:71`の実験4は、中心1点と固定4点のcoverage・depth・色の集約を次の問いにしています。

既存README:36の中心sample、top-left、厳密depth・同値先勝ちは前提です。clipと透視補間は座標・属性の扱い、受入済みの `graphics-depth-quantization` は保存深度が同じ整数になる影響を扱います。どれも今回再実装して受入を数え直す対象ではありません。

今回補うのは「同じpixelでも、どの位置で面の所属を調べるかによって、部分coverageと残るsampleの色がどう変わるか」です。2×2 pixelの固定5sceneを、中心1点と各pixelの1/4・3/4位置4点で比べます。coverageは面への所属、depth testは各sampleに残す面の選択、resolveは残った色を一つのpixel色へ集約する処理として分けます。背景を含む固定分母のRGB算術平均を教材独自のresolve規約とします。深度は平均しません。

固定sampleでの所属率は、面積を積分して求めた真の面積率ではありません。色空間・textureのaliasing・sampleごとのshading・透過・実GPUのsample配置やMSAA品質・性能は未検証です。固定の有理数模型を、実GPU仕様の再現とは呼びません。

契約・手期待を計算の実装より前に保存し、別担当がmaskとsampleごとの可視面を照合します。現在は文書と静的制作の段階で、模型・ブラウザー・配信サーバーの実行はまだ行っていません。現在状態は `status.json` に分けます。共有元・先行教材・全体集計は変更せず、自己加算は0です。

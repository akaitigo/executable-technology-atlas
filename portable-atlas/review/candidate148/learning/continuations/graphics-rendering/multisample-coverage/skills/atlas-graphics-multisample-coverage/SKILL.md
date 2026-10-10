---
name: atlas-graphics-multisample-coverage
description: Atlasの固定1点・4点の保存計算から、coverage、sample別depth、背景込みRGB平均を区別して説明する。
---

# Atlas — 固定sampleの比較へ案内する

この教材の[README](../../README.md)、[契約](../../CONTRACT.md)、[手計算](../../HAND-CALCULATION.md)、[状態](../../status.json)を先に読みます。状態に保存計算・画面確認が未実施とあれば、それを確認済みと説明しません。新しい模型・配信・ブラウザーはこのSkillから自動で起動しません。

1. **「中心が面の外ならpixelは背景だけか」**には、edge-lowのpixel(1,0)を案内します。中心は非所属ですが、四点maskは1000です。図の位置、mask、赤1点＋背景3点の平均を順に読みます。
2. **「中心が面の内なら全部赤くしてよいか」**には、edge-highの同じpixelを案内します。中心1点と四点1110の違いを見ます。sample所属率3/4を真の面積率と呼びません。
3. **「青い面を後で描けば赤が消えるか」**には、overlap-abとoverlap-baを案内します。各sampleのdepthと採用/拒否を確認し、未coverageの比較未到達nullをdepth拒否falseから分けます。
4. **「同じ最終色なら同じ処理か」**には、shared-edgeとoverlap-abを案内します。色が一致しても、共有辺での面の割当と、奥の面をdepthで拒否する経路は異なります。
5. **「赤い点だけで平均すればよいか」**には、背景も分母4に含む契約へ戻します。depthはsample別のまま保存し、集約depthは作りません。
6. **「これで実GPUの品質やtextureのaliasing改善を保証できるか」**には、[原典との対応](../../SOURCE-MAP.md)と[前提](../../PREREQUISITES.md)を示します。独自配置・固定色・算術平均の有限模型です。実GPU形式、配置、色空間、texture、shading、性能は別の観測が必要です。

保存結果を読める場合は、質問に合うscene・配置・pixel・描画段階を指定し、予想→比較→原典/実装→答えの順を崩さず案内します。欠落・改変・別条件の記録を正常結果へ補完せず、表示の拒否と古い内容の消去を確認する範囲に留めます。

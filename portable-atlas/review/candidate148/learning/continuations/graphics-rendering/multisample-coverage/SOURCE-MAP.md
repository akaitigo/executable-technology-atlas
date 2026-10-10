# Atlas — 原典と独自規約の対応

177受入の[読む順](../LEARNING_ROUTES.md)のgraphics欄には、透視補間、clip、深度量子化が並びます。今回の起点は共有 `graphics-rendering/LEARNING_PATH.md:71` の固定4sample実験です。過去の未制作一覧だけを根拠にせず、受入済みの深度量子化を差し引いた後のsamplingの問いを選びました。前提を再加算しません。

| 根拠 | 今回使う意味 | 独自に固定する部分 |
|---|---|---|
| [Microsoft Rasterization Rules — Triangle Rasterization Rules](https://learn.microsoft.com/en-us/windows/win32/direct3d11/d3d10-graphics-programming-guide-rasterizer-stage-rules#triangle-rasterization-rules-without-multisampling) | 中心位置と共有辺の所属規則 | x右/y下、固定した正向き三角形の辺関数と有限点 |
| [同 — Multisample Anti-Aliasing Rasterization Rules](https://learn.microsoft.com/en-us/windows/win32/direct3d11/d3d10-graphics-programming-guide-rasterizer-stage-rules#multisample-anti-aliasing-rasterization-rules) | 複数位置でcoverageとdepthを調べること、色の計算とsample判定の役割の違い | 四つの1/4・3/4位置、固定RGBの背景込み算術平均 |
| 同 — Hardware Support | 位置や再構成の方法は実装条件に依存する | 今回の配置をGPU標準配置や品質レベルと呼ばない |
| [手計算](HAND-CALCULATION.md) | 半平面の不等式へsample座標を直接入れる | 5sceneのmask・sample色・集約値 |

2026-10-07にMicrosoft本文を実際に読みました。ページにはauthorization案内もありますが、上記節の本文は取得できました。表示上の更新日は2026-09-08。第三者の本文・画像・実装コードは保存していないため、取得HTMLのhashはありません。URL・節・読取日とローカル前提資料のhashは[sources.json](sources.json)に分けます。

原典が示す複数位置の判定と、今回の色を平均する数式を混同しません。texture・shading・色空間・GPU実行・性能は測定しません。画面は固定計算の説明用です。

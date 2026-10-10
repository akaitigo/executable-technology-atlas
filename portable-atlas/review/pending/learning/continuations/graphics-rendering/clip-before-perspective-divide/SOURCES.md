# 原典と観測の区別

2026-10-06 JSTに公式本文を取得した。

- [Microsoft Rasterizer Stage](https://learn.microsoft.com/en-us/windows/win32/direct3d11/d3d10-graphics-programming-guide-rasterizer-stage)（更新2020-11-04）: clip、perspective divide、viewport変換、および同次clip space x,y,z,wを説明。本文の「divide by z」という表現を本モデルのx/wという数式の直接出典にはしない。
- [Microsoft D3D11_RASTERIZER_DESC / DepthClipEnable](https://learn.microsoft.com/en-us/windows/win32/api/d3d11/ns-d3d11-d3d11_rasterizer_desc)（更新2022-07-27）: 正w、x/yと±w、zと0..wのclip条件。guard band等の実装差も記載される。本モデルはside/far内の入力だけで近面だけを処理する有限契約。

NDCをx/w,y/w,z/wとする数学契約はEXPECTATIONSに明記する。交点、順序、fan、面積は手literalと独立半平面oracleで検証する。Microsoft APIは呼ばず、driver conformanceを実証しない。CPU有理数とブラウザ表示は別証拠。Subject文書は閲覧だけで計算に依存しない。既存perspective-correct-interpolationは変更しない。

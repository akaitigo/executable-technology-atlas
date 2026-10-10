# 一次資料locatorとsubset

2026-10-05公式Web確認。

- [DTCG Format Module 2025.10](https://www.designtokens.org/tr/2025.10/format/): §7.1–7.2 aliases/reference、chained/circular reference、§8 Types。参照先の実値取得と利用先への連動、循環検出を読む。JSON Pointerのrequired supportまでこのsubsetは実装していないため全spec適合を主張しない。
- [DTCG Color Module 2025.10](https://www.designtokens.org/tr/2025.10/color/): §4.1 colorSpace/components、alpha省略時1、§4.2.1 sRGB。今回は不透明sRGBだけ、hex/none/他空間/半透明は未対応。8bit丸めは独自変換方針。
- [CSS Custom Properties Level 1 §3.1](https://www.w3.org/TR/css-variables-1/#invalid-variables): 未定義参照によるinvalid at computed-value time。故障の実computedは独自CSSと実IABで別確認する。

5token JSON、CSS名、scope、fault prefix、手生成図、拒否理由は独自例。DTCG報告をW3C Recommendationやこのconverterの認証と呼ばない。本文/コード/図は転載せずlocatorを保持する。

# 一次資料と独自例の対応

2026-10-05公式Web確認。[NASA SWE-052 Ver D — Bidirectional Traceability](https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695427/SWE-052+-+Bidirectional+Traceability) §3.4 Software Designと§3.5 Software Test Procedures。

§3.4は要求と設計のlinkを変更影響の判断へ接続し、関係は多対多になり得ると説明する。§3.5はtestと要求の対応・欠落関係の確認を説明する。独自例では要求→設計→testと、その逆の別保存表を照合する。NASA原典がこの6nodeや実装の結果を保証するという意味ではない。

原典の多対多を今回の1対1に縮小した。要求の妥当性、実stakeholder承認、NASA手続適合、実queue test、製品全体の精密変更影響は未実証。本文を転載せずlocatorを保持する。

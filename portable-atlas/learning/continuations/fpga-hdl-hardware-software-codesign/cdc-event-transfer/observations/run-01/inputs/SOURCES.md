# Atlas — 原典と独自模型の対応

2026-10-07に [AMD XPM CDC Generator v1.0 / PG382 / XPM_CDC_PULSE](https://docs.amd.com/r/en-US/pg382-xpm-cdc-generator/XPM_CDC_PULSE) の公式本文を読みました。表示版は1.0 English、Release Date 2021-02-09です。狭いlocatorは Introduction と Port Descriptions の dest_pulse、Available Attributes の DEST_SYNC_FF/REG_OUTPUT です。

この製品macroは送信側のpulseを宛先の1周期のpulseへ渡すもので、feedbackや段数・reset・入力間隔の条件を伴います。本文は後続pulseとの最小gapを、送信pulseの立下りから次の立上りまで測ると説明しています。これらはそのmacroの条件です。今回の単純なtoggle模型に保証式を流用しません。今回の組合せ出力は独自の2FF＋history規約であり、製品macroの実装を再現したという主張ではありません。

[Intel 18.1 / Metastability Analysis](https://www.intel.com/content/www/us/en/docs/programmable/683068/18-1/metastability-analysis.html) は正式web読取を1回試みましたが、404Redirectorへの転送が取得できず500になりました。本文を読めたとは記録せず、連続再試行しません。今回の物理量を含まない0/1模型からMTBF等を評価しないという境界は、模型の定義自体に置きます。

## 前提と今回の増分

- [counter入口](related.html?doc=counter)：旧値から全レジスターを同時更新する。Python逐次代入との違い。
- [元のCOVERAGE](related.html?doc=coverage)：次3の pulse/level/toggle と lost event が今回の直接根拠。
- [ready-valid入口](related.html?doc=ready-valid)：同じedgeで捕捉してから送信状態を更新する。CDCは未実証と明記。
- [ready-valid実装](related.html?doc=ready-valid-code)：単一tickの捕捉・保持と、別クロックのsampleを区別する。
- [前提Skill](related.html?doc=prior-skill)：今回の問いから前提へ戻る入口。

今回の時刻、位相、初期値、検出の観測時点と終了25は [契約](CONTRACT.md) の独自規約です。2FFの論理simulation、HDL検査、物理CDC解析を同じ実証として扱いません。

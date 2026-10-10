# 一次資料と実装のbinding

閲覧確認日: 2026-10-05。文書のlocatorを示す。本文をコピーした手引きではなく、教材の判断を原典へ戻す索引。URLが版更新で変わった場合はdocument IDと節名で探す。

| ID | 公式/著者locator | 教材への対応と確認状態 |
|---|---|---|
| NBA | [Clifford E. Cummings, Nonblocking Assignments in Verilog Synthesis, Coding Styles That Kill!, SNUG 2000](https://www.sunburst-design.com/papers/CummingsSNUG2000SJ_NBA.pdf) §3–4 scheduling / §5 pipeline | [counter.v](rtl/counter.v)の`prev <= q`と[model.py](model.py)のbefore snapshot。著者の公開論文locator。今回著者サイト本文は取得未確認、同著者による[公開投稿](https://groups.google.com/g/comp.lang.verilog/c/6FQMaM_4Nls)が更新版URLと論点を説明。IEEE全schedulerの実装ではない。 |
| RESET | [AMD UG949 2026.1, Synchronous Reset vs. Asynchronous Reset](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Synchronous-Reset-vs.-Asynchronous-Reset?contentId=6i5eyzaTWF8I0_fGz0giBw) | Web本文確認。pulse caseのreset入力仕様の検討に使う。モデルはrecovery/removal、metastability、routing costを測らない。 |
| SIM | [AMD UG900 2026.1, Vivado Design Suite User Guide: Logic Simulation](https://docs.amd.com/r/en-US/ug900-vivado-logic-simulation) behavioral / post-synthesis / post-implementation simulation | Web目次確認。[tb.v](rtl/tb.v)のNBA後観測、RTL simulationと物理timing simulationの区別。今回はPythonモデルのみ実行。 |
| SYN | [AMD UG901, Synthesis](https://docs.amd.com/r/en-US/ug901-vivado-synthesis) HDL coding techniques / registers / FSM / RAM | 公式document locator。今回この版本文未確認。RTLが合成可能か、LUT/FF/BRAM/DSPへどう写るかは未実証。 |
| TIM | [AMD UG903 2026.1, Using Constraints](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints) Defining Clocks / I/O delay / CDC / multicycle / false paths | Web目次確認。波形が論理的に正しいだけではsetup/hold slackを証明しない。 |
| AXI | [AMD AMBA AXI4 Interface Protocol](https://www.amd.com/en/products/adaptive-socs-and-fpgas/intellectual-property/axi.html) AXI4 / AXI4-Lite / AXI4-Stream | 検索索引確認。softwareがレジスタを書いた時点と回路が捕捉する時点を分ける次教材の入口。今回bus未実装。 |
| HLS | [AMD UG902, High-Level Synthesis](https://docs.amd.com/api/khub/documents/5tAySqTg~5WxiLlY_rRv7g/content) interface synthesis / C-RTL co-simulation | 2015.1の公式PDF検索索引確認、現行ツールAPI保証には使わない。partition / pipeline / interfaceの問いへ。 |

仕様の正本は[README](README.md)の契約と[oracle.py](oracle.py)の遷移表。[cases](cases.json)が入力、[raw](evidence/raw.json)が出力、[run](evidence/run.json)が実行環境・入力/実装/原典索引のSHA-256、[integrity](evidence/integrity.json)が教材と成果物のbinding。公式資料の本文取得成功と、locatorだけの記載を区別した。

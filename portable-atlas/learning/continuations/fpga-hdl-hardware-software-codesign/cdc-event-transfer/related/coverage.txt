# Subject全体の学習ロードマップと未教材範囲

Subject: FPGA・HDL・ハードウェア協調設計。今回完成するのは有限1unit「クロックと2bit counterの同時更新」。Subject完成、HDLツール実行、合成、timing closure、実機検証の証明ではない。

前提は2進数とmod 4、条件分岐、時系列表。ソフトウェアの逐次代入に慣れていれば「レジスタはedge前の値を同時に読む」を最初の観察軸にする。[UI](index.html)→[契約と実装](README.md)→[原典索引](SOURCES.md)を通って次の問いへ進む。

| 主要概念・未教材coverage | 今回から判断できること / 未解決の問い | 次の具体的実験 | 公式locator |
|---|---|---|---|
| 組合せlogic / FF / latch / FSM / Verilog・SystemVerilog・VHDL / signedness・幅・X/Z / event scheduling | qとprevは別の状態。next-stateをそのままprevに書くと遅延が消える。X初期値、delta-cycle race、latch inference、case完備性は未検査 | **次1:** 同じcounter RTL/tbを既存HDL simulatorで実行しモデルと照合。2stage FSMでdefault漏れ・幅変換・blocking variantを波形比較 | [UG901](https://docs.amd.com/r/en-US/ug901-vivado-synthesis)、[UG900](https://docs.amd.com/r/en-US/ug900-vivado-logic-simulation)、[NBA](https://www.sunburst-design.com/papers/CummingsSNUG2000SJ_NBA.pdf) |
| FPGA fabric / LUT・FF / BRAM・DSP / IP / synthesis / place-route / constraints / setup・hold・slack / clock resources / I/O・pin / PPA | mod4の論理wrapは示せるがFmaxや利用FF数を断定できない。合成が正しい機能でもtimingを満たすか | **次2:** 同じcounterを合成しnetlist/resourceを確認、clock periodを変えてSTA比較。pipelineあり/なしの小adderでcritical pathとlatencyを比べる（今回はツール/boardなし） | [UG901](https://docs.amd.com/r/en-US/ug901-vivado-synthesis)、[UG903](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints) |
| clock/reset domains / async assertion・sync deassertion / CDC・RDC / synchronizer / metastability・MTBF / async FIFO / Gray code | clock間pulseはsync resetで消える。async resetの論理応答は見えるが安全なdeassertionは証明できない。単bitとbusのCDCは同じか | **次3:** 2clockのpulse/level/toggle転送を対比しlost eventを数える。2FFの論理simulationではmetastability確率を測れないことを示しCDC reportと照合、後にGray FIFO full/empty境界へ | [UG949 reset](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Synchronous-Reset-vs.-Asynchronous-Reset?contentId=6i5eyzaTWF8I0_fGz0giBw)、[UG903 CDC](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints) |
| hardware/software partition / MMIO・register map / AXI ready-valid・backpressure / DMA・interrupt / cache coherence / driver / HLS・co-simulation / bandwidth・latency | softwareが値を計算した順序とhardware edge捕捉を分ける入口にはなる。今回は実bus・CPU連携・accelerator速度向上を示さない | **次4:** AXI-Lite風の有限register mapとsoftware driver modelでwrite→捕捉→readを照合、stallとreset途中のtransactionを注入。次にDMA coherencyとHLS C/RTL co-sim、転送込み性能へ | [AXI](https://www.amd.com/en/products/adaptive-socs-and-fpgas/intellectual-property/axi.html)、[UG902 interface](https://docs.amd.com/api/khub/documents/5tAySqTg~5WxiLlY_rRv7g/content) |
| testbench / assertions・formal / functional coverage・random stimulus / debug・ILA / equivalence / board bring-up・power・configuration・security | 独立oracleが128通りの1stepを検査し意図異常を検出。RTL等価性、全入力列、UVM、formal proof、故障注入、実機ILA、bitstream更新・secure bootは未実証 | 次1の後、reset/enable/rolloverのassertionをRTLで追加、cover未達を残す。次2–4の検証成果へ同じinput/source bindingを適用 | [UG900 verification](https://docs.amd.com/r/en-US/ug900-vivado-logic-simulation)、[UG949](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology) |

実務では仕様書にreset優先順位、enableがどのregisterを止めるか、入出力の捕捉時点、出力のlatencyを書く。この教材のenableはqだけを止め、prevは毎edgeで更新する。async版は比較用の別契約であり、sync oracleへの不一致を一律bug扱いしない。

限界: Pythonの既知初期状態、理想event、0/1だけ、最大64event、同時入力はedge直前に確定済み。物理時間ではなく任意時刻単位。setup/hold違反、clock jitter、recovery/removal、analog metastability、FPGA power-on、gate-level timingをモデル化しない。install・Docker・外部サービス・課金・公開は今回ない。各未教材は今後の候補で、実行済みを意味しない。

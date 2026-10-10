# 先に固定する有限契約

ADDとADDIだけを構造化JSONで受ける。機械語decoder、LOAD/STORE、branch、例外、HDL、実CPUは対象外。32個のregisterはunsigned表示、x0は常に0。ADDはrs1+rs2、ADDIはrs1+signed 12-bit immediate（-2048..2047）、結果をmod 2^32とする。初期値は32個の0..4294967295整数、x0=0。bool、float、文字列の数値を拒否。programは0..12命令、未知fieldも拒否する。

## 独自のcycle契約

cycle行はcycle開始時のIF/ID/EX/MEM/WB。cycle1のIFにI1を置く。空programは0cycle。IFは有限配列を順にfetch。IDはregisterを読んでEXへのoperandをlatchする。EXは一度だけ演算。MEMはmemory操作をせずresultを運ぶ1cycle。WBは非zero rdへcommit。全命令はx0書込でもWBまで進み、完了数に数える。

各cycleでは旧pipelineをsnapshotし、WB commit→EX計算→ID読出しの順で評価する。WBとIDが同cycleならIDは新register値を読む。次stateはまとめて置換し、現在EXの計算を同cycleのEX operandへ使い回さない。

- none: IDでlatchしたoperandをEXでそのまま使う。未解決RAWでも進む故障対照。
- stall: IDの実際のsource（ADDIはrs1だけ）が旧EXまたは旧MEMの非zero rdと一致したらIF/IDを保持、次EXへbubble。EX→MEM、MEM→WB、WB retireは進む。WBは既にcommitしたため待たない。
- forwarding: stallなし。EXの各sourceは旧MEM（EX/MEM latch）のresultを最優先、次に旧WB（MEM/WB latch）、次にIDでlatchした値。x0は常に0、rd=0をproducerにしない。新しいproducerを優先する。

この固定stage数でのみcyclesを比較する。clock周期、IPC一般論、実機の速さは推論しない。sequential oracleはinstruction順にregisterを直接更新し、pipeline関数を呼ばない。

## 実装前の手計算

全初期値0。I1=ADDI x1,x0,5、I2=ADD x2,x1,x1、I3=ADDI x3,x2,-1。

| cycle | none / forwarding (IF ID EX MEM WB) | stall (IF ID EX MEM WB) |
|---|---|---|
|1|1 - - - -|1 - - - -|
|2|2 1 - - -|2 1 - - -|
|3|3 2 1 - -|3 2 1 - -（待つ）|
|4|- 3 2 1 -|3 2 - 1 -（待つ）|
|5|- - 3 2 1|3 2 - - 1|
|6|- - - 3 2|- 3 2 - -（待つ）|
|7|- - - - 3|- 3 - 2 -（待つ）|
|8|終了|- 3 - - 2|
|9|終了|- - 3 - -|
|10|終了|- - - 3 -|
|11|終了|- - - - 3|

sequentialのx1,x2,x3は5,10,9。noneは5,0,4294967295で不一致。forwardingはI2のEXでMEMの5を両sourceへ、I3のEXでMEMの10を使い7cycle。stallは4回待って11cycle、5,10,9。

追加の事前期待値: independent=3命令で7cycle、x1=5,x2=7,x3=9。priority（ADDI x1,0,1; ADDI x1,x1,1; ADD x2,x1,x1）は正常x1=2,x2=4、noneは1,0、stall11cycle。two-source（x1=3; x2=4; ADD x3,x1,x2）は正常7、none0、stall9cycle。WB-gap（x1=5; x4=1; x5=2; ADD x2,x1,x1）は全modeでx2=10、8cycle。x0-write（ADDI x0,0,9; ADDI x1,0,2）は全modeでx0=0,x1=2、6cycle。immediate-boundary（ADDI x1,0,-2048; ADDI x2,0,2047; ADD x3,x1,x2）は正常x3=4294967295、none0、stall9cycle。wrap（初期x1=4294967295; ADDI x2,x1,1）はx2=0、5cycle。emptyは0cycle。

## 出典の適用範囲

[RISC-V RV32I 2.1](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html) のProgrammers' ModelとInteger Computational Instructionsを参照（2026-10-05 UTC閲覧）。ISA規則のみ根拠にする。
[Cornell CS3410 Pipelining & Performance](https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/pipelining.html#hazards) はstageの重なりとhazardの導入を参照。同ページはcontrol hazardの例を挙げ、hazard対策を授業範囲外とする。ここでのRAW、WB順序、forwarding優先順位は独自設計であり、同資料の実装とは主張しない。

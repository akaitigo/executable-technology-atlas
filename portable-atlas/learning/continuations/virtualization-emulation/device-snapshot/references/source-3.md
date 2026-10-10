# この教材が定義するTiny8 ISA

これは教材作者が定義した独自ISAであり、x86/ARM/RISC-V/CHIP-8の互換実装ではない。ISA仕様の一次資料はこの文書。広いemulation/virtualization概念の原典は[SOURCES](SOURCES.md)へ。

状態はA8bit unsigned、PC8bit address、read-only memory256byte、halt flag。入力programをaddress0から配置し、残りを0x00で埋める。padding0x00はNOPではなくillegal opcode。memoryはcode/dataを区別せず、JZでoperand byteへ飛ぶこともできる。静的命令境界を強制しない。

| opcode | length | 意味 | 次PC |
|---|---|---|---|
| 0x10 LOAD imm8 | 2 | A=operand | PC+2の下位8bit |
| 0x20 ADD imm8 | 2 | A=A+operandの下位8bit | PC+2の下位8bit |
| 0x30 JZ addr8 | 2 | A==0ならabsolute addrへ。flag registerはない | takenならoperand、else PC+2の下位8bit |
| 0xFF HALT | 1 | halt=true、Aを変えない | PCを変えない |

operand fetch addressはPC+1の下位8bit。例: PC255でLOADならoperandはmemory0、次PCは1。illegal opcodeは実行時拒否、stateを変更しない。budgetは1..64、HALTも1step。budget最後の命令がHALTなら正常終了。HALT前にbudgetを使い切ればstep_budget拒否（有限traceを残す）。fault命令はcommitされたstepに数えず、diagnosticに残す。

入力は`program`=1..256byteのlist（各integer0..255）、`pc`/`a`=integer0..255、`budget`=integer1..64のobjectだけ。bool/float/extra key/外部fileやVM path拒否。input拒否はtraceなし。実行拒否は直前までのtraceあり。

naive-unboundedは教材の意図異常: ADDにPythonの任意精度integerをそのまま使い、PC+1/PC+2もwrapしない。LOADはbyte値、JZはA==0。PC/operandが256以上なら明示的oob拒否し、両variantとも同じ有限budgetを強制する。無限loopをhost上で走らせない。

[手計算](handtrace.json)の中心program `10 FF 20 01 30 08 10 63 FF`: 正常Aは255→0でJZ8をtaken、HALT後A0/PC8/4step。異常A256ではbranch不成立、LOAD99を実行してA99/PC8/5step。小さい観測差でもguest仕様を破る。

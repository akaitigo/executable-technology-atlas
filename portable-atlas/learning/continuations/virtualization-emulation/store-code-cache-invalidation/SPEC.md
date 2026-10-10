# STOREを持つ独自Tiny8仕様（この単元の正本）

[元Tiny8](../../../subjects/virtualization-emulation/SPEC.md)のread-only memoryを、この単元ではmutableな256byte memoryへ拡張する。他の命令、unsigned A/PC各8bit、operand fetch/PC加算の256 wrap、HALTのPC保持、padding 0x00 illegalを維持する。独自教材ISAであり実ISAの互換性はない。

| opcode | 長さ | commit後の効果 |
|---|---|---|
| 0x10 LOAD imm8 | 2 | A=operand, PC=(PC+2)&255 |
| 0x20 ADD imm8 | 2 | A=(A+operand)&255, PC=(PC+2)&255 |
| 0x30 JZ addr8 | 2 | A==0ならPC=operand、他はPC+2 wrap |
| **0x40 STORE addr8** | **2** | **memory[operand]=A、A保持、PC+2 wrap** |
| 0xFF HALT | 1 | halt、A/PC保持 |

STOREのoperandは書込み前に取得する。書込みでopcode/operandを区別しない。JZはoperand byteにも飛べる。flags、JMP、新しいaddress spaceは追加しない。

入力は正確にprogram/pc/a/budgetの4key。programは1..256個のinteger byte、pc/aはinteger0..255、budgetはinteger1..64。bool/float/extra key/外部pathを拒否する。input拒否は状態・memory・traceなし（表示PC/Aは0のsentinel）。illegal opcodeは直前stateを保持して未commit命令PC/opcodeをdiagnosticへ残す。budgetはHALTも1stepに数える。最終枠HALTは成功、HALT前の消費完了はbudget拒否。host例外とは区別し、有限batchのexit0は全guestの正常HALTを意味しない。

## 比較する3実装

fetchは毎命令memoryからopcode/operandを取得する。invalidateはguest bytesをPython dict/listのdecoded blockに保存し、STOREが重なるbyte addressを含む全cache blockを失効する。staleは同じblock処理で意図的に失効だけを省く。native JITはない。

blockは開始PCからLOAD/ADDを連続decodeし、JZ/STORE/HALT/illegalで終わる（最大64命令）。STORE後は現在blockを離れて次PCからlookupする。cache単位は開始PC、依存addressはopcodeとoperandの両方。wrap block255はaddress {255,0,1}。範囲は閉区間[255,255]＋[0,1]であって[0,255]ではない。block8のaddressは{8,9,10}、write11は非重複。block20の{20,21,22}をwrite9で失効させない。

prewarmはケースに書いた開始PCだけを実行前decodeする。decodeはguest命令実行ではなくA/PC/memoryを変えない。STOREはcache内の全依存addressを調べる。writeと同値でも失効する定義（同値ケースは今回未検証）。branch先だけでなくoperandも依存範囲。

## 実行前固定表

[expected-table.json](expected-table.json)はproducer初回実行前に固定した命令ごとのPC/A、opcode/operand、書込みaddress/old/new、最終stateと期待失効blockのliteral表。[contracts.json](contracts.json)はinput bytesとprewarm開始PC。checkerはproducerをimportせず、decoder/cacheを再利用しない。literal差分から全memoryを照合する。

中心program: `10 07 40 09 10 00 30 08 10 01 FF`。block8を事前decodeし、STORE9でoperand1→7。LOAD0後JZ8。fetch/invalidateはA7、staleは事前operand1を使いA1。PC10 HALT、6step、memory9=7は全実装共通。メモリ一致だけではdecode整合性を証明できない。

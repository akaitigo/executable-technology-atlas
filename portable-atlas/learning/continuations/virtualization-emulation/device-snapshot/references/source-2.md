# Virtualization・emulationを学ぶ入口 — guestの8bitは誰が守る？

有限1教材。Python標準libraryで作者定義のTiny8 ISAを実装・実行し、正常とwidthを忘れた異常版を比較する。[UI](index.html)は保存原票をreplayする。実ISA互換・hypervisor・実VM boot・isolationは未実証。分野全体の完成ではない。

**前提 → 主要概念・仕組み:** byteは0..255、Aはregister、PCは命令address。memoryからfetch→decode→executeし状態を更新する。host Python integerはguest8bitを自動的に守らない。A/PC/operand addressをguest仕様でwrapする必要がある。[SPEC](SPEC.md)のencoding表が作者定義の一次資料。

| opcode | 命令 | 正常動作 |
|---|---|---|
| 10 hex | LOAD imm8 | A=imm、PC+=2を8bit wrap |
| 20 hex | ADD imm8 | A=(A+imm)の下位8bit、PCもwrap |
| 30 hex | JZ addr8 | A==0ならabsolute addr、else PC+=2 |
| FF hex | HALT | A/PCを変えず終了。1step数える |

**予想 → 操作 → 比較:** [UI](index.html)で「A255に1をADDした後、JZ8はtakenか？」を予想し、caseを選んでstepを進める。register・PC・fetch memory・正常/異常trace・独立oracleを比較。原典/実装を開いてから答えへ。中心programは`10 FF 20 01 30 08 10 63 FF`。正常はA255→0、JZ8→HALT、最終A0/PC8/4step。異常はA256でJZ不成立→LOAD99→HALT、最終A99/PC8/5step。

**今回の実装・正常異常:** [emulator.py](emulator.py)が実interpreter。[oracle.py](oracle.py)はemulatorをimportせず、successor・advance-two・循環addition tableで独立期待traceを構成する（同じmask式を共有しない）。[handtrace](handtrace.json)の中心4stepとPC254 wrap2stepは手記の別anchor。全65536ADD、PC/operand wrap256位置、JZ taken/not-takenを検査するが、全program列の形式証明ではない。

naive-unboundedはA/PCの幅を忘れる意図異常で、実行budget自体は正常と同じ。PC254からLOAD42すると正常PC0へ戻ってHALT、異常PC256でpc_oob拒否。PC255のoperand fetchは正常memory0、異常address256でoperand_oob拒否。illegal opcode/operandへのjump/loop budget拒否も保存する。

入力は`{"program":[16,255,32,1,48,8,16,99,255],"pc":0,"a":0,"budget":16}`のみ。program1..256byteのlist、各byteとpc/aはinteger0..255、budgetはinteger1..64。bool/float/extra key・外部file/VM path拒否。programをaddress0から配置し残りを0x00で埋める（0x00はillegal opcode）。A/PCの初期値は入力で明示。read-only memory、STORE/flagsなし。fault命令は未commit、直前までのtraceを残す。

このdirectoryで:

```sh
python3 -B runner.py
python3 -B runner.py --input-json '{"program":[48,0],"pc":0,"a":0,"budget":8}' # step_budget拒否 exit2
python3 -B checker.py
python3 -B route.py emulator
python3 -B route.py vm-boot # 未対応 exit2
python3 -B preview.py # dynamic 127.0.0.1 URLを開く。終了はCtrl-C
```

正常HALTはexit0、input拒否と正常variantのexecution拒否はexit2。意図異常版だけの拒否は比較成果で、正常HALTならtop-levelはaccepted。budget最後のHALTは許容、HALT前にbudgetを使い切ると拒否。通常runner/checker/route/optionなしobserveはread-only。原票再観測の明示依頼にだけ`python3 -B observe.py --write-evidence`、binding更新にだけ`python3 -B checker.py --seal-evidence`。検査失敗はexit1。原票のhash更新を再実行と呼ばない。

[raw](evidence/raw.json)はinput・memory256byte・2variantのbefore/fetch/after/fault・独立oracle。[run](evidence/run.json)は実行時刻/環境/input/source/raw/図digest。[register図](evidence/register-trace.svg)はrawから生成した図でcaptureではない。[実IAB QA](evidence/ui-qa.json)がcapture保存・ownedserver終了を記録する。memoryは実guest hardwareではなくPython byte列で、host memory protectionの証拠ではない。

**実務判断 → 限界 → 原典:** guest状態幅、instruction/fetch境界、branch条件、HALT/fault/budget優先順位を仕様で判断できる。guest cycle精度、実machine boot、device/interrupt、hypervisor isolationは判断できない。[全Subject coverageと次の4実験](COVERAGE.md)でISA拡張→translation→full machine→hardware virtualizationへ進む。[公式locator](SOURCES.md)と[専用skill](skills/atlas-virtualization-emulation/SKILL.md)から既存runner/checker/UIへ戻れる。旧教材・Portal/Core/Graph・新依存・Docker・host設定・global install・commit/push/公開を今回変更しない。

# Atlas — 起動時に初期値をどこへ置くか

この契約と手計算表を、計算の実装より先に固定する。対象はPython標準ライブラリの有限byte模型。実MCU、CPU命令、linker、ELF、flash、RTOS、装置の初期化を実行した結果ではない。

## 前提と問い

byte、配列の添字、read/write、半開区間 `[start,end)` が前提。既存のTiny8は命令の実行、ISR教材は共有更新、queue教材は引渡しを扱う。本教材はそれらを作り直さず、ROMにある初期値とRAMで使う値の間を学ぶ。

予想→配置図と操作順→正常／省略／越境／早期読取りの比較→原典と実装→答え→実務判断の順で読む。実務上の問いは「配置先の指定だけでRAMの初期化まで済んだと言えるか」「最後のRAMが正しくても、早く読んだ値は正しかったか」である。

## 固定配置と単位

- ROM、RAMは各16 byte。架空の基底はROM `0x1000`、RAM `0x2000`。実アドレス空間へのアクセスではなく、領域名と0〜15のoffsetを使う。
- ROM全体は `d0 d1 d2 d3 11 22 33 44 e8 e9 ea eb ec ed ee ef`。読み取り専用として全条件で不変を検査する。
- 初期RAMは `a5 a5 a5 a5 a5 a5 cc a5 a5 a5 a5 a5 cc a5 a5 a5`。A5とCCは合成fixtureであり、電源投入時の実RAM値を意味しない。
- `.data` はROM offset `[4,8)` の4 byteをRAM `[2,6)`へコピーする。模型上のLMAは `0x1004`、VMAは `0x2002`。一対の領域とoffsetの対応であり、MMU変換や実linkerの出力ではない。
- `.bss` はRAM `[8,12)` の4 byteを0にする。ROMからコピーする初期byteは割り当てない。
- RAM offset6と12は保護用byte。`.data` と `.bss` は重ならず、間にも保護用byteがある。他のRAM byteも含め全16 byteを照合する。
- コピーはoffsetの小さい順、ゼロ化も小さい順。正しい終端は含まない。ROMへwriteしない。

## 固定7条件

| ID | 操作順と違い | mainが読むdata / bss | write数 | 分類 |
|---|---|---|---:|---|
| copy-zero-main | copy→zero→main | 11 22 33 44 / 00 00 00 00 | 8 | 正常 |
| zero-copy-main | zero→copy→main | 同上 | 8 | 正常 |
| skip-copy | zero→main | a5 a5 a5 a5 / 00 00 00 00 | 4 | 意図的な初期化不足 |
| skip-zero | copy→main | 11 22 33 44 / a5 a5 a5 a5 | 4 | 意図的な初期化不足 |
| main-early | main→copy→zero | a5 a5 a5 a5 / a5 a5 a5 a5 | 8 | 意図的な早期読取り |
| copy-one-past | 終端を含むcopy→zero→main | 11 22 33 44 / 00 00 00 00 | 9 | 意図的な越境 |
| empty-regions | data/bssの長さを両方0にしcopy→zero→main | 空 / 空 | 0 | 空領域の正常境界 |

非重複なのでcopyとzeroの間に必須の先後関係はない。mainは両方を終えた後に置く。mainはこの模型で指定範囲を読む1回の観測であり、実Cのmain呼出しではない。

copy-one-pastはROM offset8のE8をRAM offset6へ余分に書く。後のbssゼロ化はこの保護用byteを隠さない。mainが名前付き変数の期待byteを読めても、越境なしとは結論しない。故障を入力拒否や正常成功へ分類しない。

main-earlyはその時の読値を保持する。後のRAMは正常配置へ達するが、過去のmain読値を更新しない。空領域はそれぞれ `[2,2)` と `[8,8)` でありwrite0、読値は空配列。4 byteの初期化が実行された意味ではない。

## 観測と独立検査

初期状態、各操作後の全RAM、全writeのphase・offset・元のbyte・新byte・コピー元offset、main時の両領域・copy/zero完了状態・保護用byte、最終RAM、ROM不変を記録する。7条件のwriteは計41件、操作後の境界は19件、初期状態込み26件、main観測7件。

`main.initialized` は、両処理の完了・mainの期待読値・保護用byteの保持という、本教材の初期化契約を全て満たすかを表す。名前付き変数のbyteが合うだけの意味ではない。copy-one-pastは読値が合っても保護用byteが壊れたためfalse、空領域のtrueは0 byteの契約を満たした意味である。

手計算表は固定の配列とwrite列で保存し、計算の実装を呼ばない。検査は全結果をその表へ照合し、別の半開区間集合による書込み範囲とも比較する。最後の値だけでは合否を決めない。

入力は固定fixtureの正確なschemaと7 case IDだけ。boolを整数として受け入れない。範囲外、逆転、重複、保護用byteとの重なり、未知操作、byte範囲外、不足／余分なfieldはwrite前に拒否する。拒否時のwrite数は0、mainは未到達のnull。意図的な越境はこの入力拒否を迂回する汎用機能ではなく、固定された1故障caseだけで実行する。

## 実行条件と限界

独立手期待と実行前レビュー後、調整済み枠でfresh資源確認を行う。既存Pythonの1子、同じ子でnice実値10、計算5秒＋回収猶予2秒、再試行0。開始前失敗・計算失敗・期待拒否・故障比較・回収を分離する。旧教材のPID例外を今回へ無条件継承しない。実画面は既存の同じブラウザーページを再利用し、この教材側で起動しない。

GNU ld原典はVMA/LMAとROMからRAMへコピーする例、bssゼロ化の根拠に限定する。数値、A5/CC、空領域、操作順、保護用byte、mainの観測は教材独自の契約。C言語全体の初期化規則、実MCU reset vector、stack、constructor、HAL、DMA/cache、起動時間、安全性は保証しない。

---
name: mark-sweep-roots
description: 合成heapでrootからの到達性をmark/sweepの各stepと独立oracleから学び、cycle・root移動・root見落としの誤回収を比較する。
---

# 合成heapのmark/sweep

READMEとCONTRACTを読む。Python標準libraryだけでserve.pyを起動し、自分の動的localhostを開く。既存server/tabへ操作しない。

rooted-cycle/全rootでlive誤回収を予測して実行し、stepを初期へ戻してFIFO queue、gray/black、sweep keep/resetを追う。D/Eが互いを参照していてもrootから届かない理由を説明する。root見落としでABCが誤回収される反例を比較する。

masked-root・root空・全root・自己cycle・空heapで同じ説明を試す。移動前後は未回収graphの独立snapshotであり、回収済みobjectの復活ではない。Crafting Interpretersのroot/mark/sweep節と独立Warshall oracleへ戻る。

verify.py/route.pyは既存raw/receiptをread-onlyで検証する。旧証拠を上書きしない。graphは数学simulationであり、実memory、allocator、停止時間、速度、moving/generational GCを検証したとは言わない。実験後は自分のserver/tabだけを閉じる。

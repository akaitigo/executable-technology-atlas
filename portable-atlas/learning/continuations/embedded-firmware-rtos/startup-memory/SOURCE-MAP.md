# Atlas — 原典と前提の対応

GNU ldオンラインマニュアルの版ページはGNU Binutils **2.47**と記載する。2026-10-06の取得本文をsources/へ保存し、[取得記録](sources/retrieval-approved.json)のSHA-256で固定した。固定release archiveや実行中のlinkerの版ではない。通常環境のDNS取得失敗は[初回記録](sources/retrieval.json)へ保持し、正規承認された読取で取得した。自動再試行は行っていない。

- [Basic Linker Script Concepts §3.1](https://sourceware.org/binutils/docs/ld/Basic-Script-Concepts.html)：VMAは実行時の配置先、LMAはロード時の配置先。ROMからRAMへ初期値をコピーする例を本教材の2領域へ対応させる。[保存本文](sources/Basic-Script-Concepts.html)。
- [Output Section LMA §3.6.8.2](https://sourceware.org/binutils/docs/ld/Output-Section-LMA.html)：ATによるLMA指定と、ROMのdataコピー・bssゼロ化のコード例。終端未満の範囲を読む。[保存本文](sources/Output-Section-LMA.html)。
- [版とライセンスの案内](sources/index.html)：GNU Free Documentation License 1.3の原文書。保存本文は変更していない。



Tiny8の配置・命令の実行は `learning/subjects/virtualization-emulation/README.md` と `COVERAGE.md`、割込み/queue/priorityはembedded入口と2継続教材へ戻る。今回これらの実行を再制作しない。既存build教材のlinker依存に関する説明も、ROM→RAM初期化の実測とは扱わない。索引が挙げたreference repo名は、指定private-code位置では未検出であり、別の場所にも存在しないとは断定しない。

半開範囲の具体値、保護用byte、RAMのA5、mainの合成観測、空領域、故障分類は[本教材の契約](CONTRACT.md)。原典から実機の起動成功や安全性を推測しない。

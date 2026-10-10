# 原典と作者規約

[QEMU公式Migration framework](https://www.qemu.org/docs/master/devel/migration/main.html)を正式webで2026-10-07に読みました。

- 冒頭と「Saving the state of one device / General advice for device developers」：継続に必要な装置の状態は、見えるレジスターだけに限らないという概念を接続します。
- 「VMState / Versions」：保存欄と形式の版を明示するという観点を参照します。

本教材のsnapshotはQEMU migration streamやVMState形式ではありません。周期3、polling、tick→timer→命令順、4切断点、JSON schemaとmissing拒否は独自規約です。QEMUが本教材のすべての拒否規則や結果を保証するとは主張しません。実QEMU/HVF/live migrationは実行しません。

原典URL・読取範囲と共有前提のSHAは[sources.json](sources.json)へ保存します。手で固定した答えは[手計算](HAND-CALCULATION.md)、仕様の正本は[CONTRACT](CONTRACT.md)です。原典を読むこととソフトウェアを実行したことを分けます。

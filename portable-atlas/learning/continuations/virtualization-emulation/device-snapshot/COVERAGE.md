# 目標16：装置状態を含む保存・復元

183受入時点の新しい問いは、PC/A/memoryが同じでも装置の途中状態が落ちると、その後の観測が変わることです。目標16:218–223と共有 `subjects/virtualization-emulation/COVERAGE.md` の次3を根拠にします。

Tiny8の8bit幅・命令境界は前提です。既存 `store-code-cache-invalidation` はSTOREとdecode cacheの整合を扱い、deviceを未実証としています。これらを新規原理として数えません。

本単元は周期3の小装置、固定10命令、4切断点に限ります。継続／完全JSON復元／device欠落を比較し、counterとpendingの保存必要性、snapshotのschema拒否と意図故障の区別を判断します。

作成時点は契約・手期待の固定段階で、対象計算・実画面は未実施です。現在状態はstatus.jsonへ分離します。実VM、QEMU、HVF、互換性、隔離、物理時間、live migrationは未検証、分野全体の完成は主張しません。

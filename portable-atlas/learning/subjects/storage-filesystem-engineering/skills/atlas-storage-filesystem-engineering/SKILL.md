---
name: atlas-storage-filesystem-engineering
description: この有限write-new/atomic replace教材の実temp file・reader length/hash・truncate例外反例を既存runner/checker/timeline UIへrouteする。block CoW、power-loss durability、disk修復やhost設定には使わない。
---

rootは`../..`。[README](../../README.md)で有限input/ownership、[coverage](../../COVERAGE.md)で次の4実験、[sources](../../SOURCES.md)で原典bindingを読む。

- `python3 -B route.py replace|verify|timeline|sources`は既存runner.py/checker.py/index.html/SOURCES.mdへrouteする。別runnerや新依存を増やさない。
- `python3 -B runner.py`またはREADMEの`--input-json`はmodule内の新規owned tempだけで実行しcleanupする。外部pathを与えない。拒否exit2とintentional exceptionを記録した正常な反例を区別。
- `python3 -B checker.py`は通常read-only。原票再観測の明示依頼にだけ`python3 -B observe.py --write-evidence`。binding更新の明示依頼にだけ`python3 -B checker.py --seal-evidence`。hash更新を新しい実観測と呼ばない。
- [UI](../../index.html)は予想→event replay→path/held reader/candidateとoracle比較→原典/実装→答え。既存文書viewerを使う。previewはdynamic loopback一時serverで専用processを終了する。
- [raw](../../evidence/raw.json)/[run](../../evidence/run.json)の時刻・環境・digest・cleanupを示す。file/directory fsyncのcall/returnを電源断durabilityの証明にしない。別tempへの書込戦略をphysical block CoW実証と呼ばない。

block-cow、power-loss、raid、repair、mount、kernel-driver、backupや任意未定義topicはunsupported/exit2で[coverage](../../COVERAGE.md)の具体的な問い・公式locatorへ案内する。依存追加、OS設定、外部data、global install、課金、公開へ拡張しない。

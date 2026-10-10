---
name: atlas-operational-data-stores
description: このmoduleの実SQLite versioned KV教材で、lost updateとexpected-version更新拒否、型・未知key・ABA境界を説明・再現する。Redis製品、cache/document/graph全体、lockingや分散性能の質問は未教材範囲を確認する。
---

# Versioned KV有限教材

module rootはこのdirectoryの2階層上。[README](../../README.md)と[Coverage](../../COVERAGE.md)の範囲を読む。

- 既存観測の説明：`../../evidence/stdout.json`のSQL/rowcount/state traceと`../../evidence/run.json`のruntime/input/source bindingを読む。一次資料は`../../sources.json`。
- 検証：`python3 -B ../../verify.py`。`python3 -B ../../observe.py`も読取り専用。どちらも原票更新を伴わない。
- 新しい実観測を求められた場合だけ`python3 -B ../../observe.py --write-evidence`。固定合成値・2接続・逐次SQLを再実行し、成功原票を更新する。
- 画面：`../../index.html`の予想、case比較、trace step、答えを使う。HTTP起動はREADME。UI再生と実SQLite観測を区別する。
- stale/unknown更新は実SQL rowcount0、型拒否はAPI側で更新SQLなし。ABAの保護はversionが増え続ける同じkey lifetime内だけ。削除/recreateでversionを戻す反例も説明する。
- Redis、TTL/cache/document/graph、分散CAS、locking、並列性能、durabilityはこのmoduleでは未検証と答える。必要な実環境/試験を示し、Subject全体完成や製品保証を推論しない。


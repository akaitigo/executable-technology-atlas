# 原典と独自policy

2026-10-06 JSTに公式本文を確認。Python文書の表示版3.9.25と実runtime版は分け、実Python/SQLite版は各raw environmentへ保存する。第三者本文やcode例を複製しない。

- [Python3.9 sqlite3](https://docs.python.org/3.9/library/sqlite3.html)、connect / execute / fetchall / set_trace_callback / rowcount / Controlling Transactions。:memory:、parameter binding、SQL traceとSELECT rows、autocommitを読む。SELECT rowcount=-1を件数へ置換しない。
- [SQLite UPDATE](https://www.sqlite.org/lang_update.html)、§2 Details。WHEREに一致する原本行を更新し、valueとversionを同じstatementで変更する。
- [SQLite SELECT](https://www.sqlite.org/lang_select.html)、Simple Select Processing。client refillとharness原本auditのrowsを分ける。

t<expires_at、TTL1..10、fake monotone integer、通知欠落、single keyのcacheはこの教材の独自policy。SQLite公式のTTL機能や製品Redisのexpirationを実証したとしない。

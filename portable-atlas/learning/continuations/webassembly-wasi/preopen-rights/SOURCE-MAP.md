# Atlas：WASI原典と実験条件の対応

- 公式WASI `snapshot-01`：`sources/snapshot-01-typenames.witx` のerrno・rights・fdstat・prestat、`snapshot-01-api.witx` のfd_prestat_get、fd_fdstat_set_rights、path_open、fd_read、fd_close。URLと本文SHAは `sources/fixed-tag-retrieval.json`。
- 固定uvwasi `v0.0.23`：`uvwasi-v0.0.23.c` 967–1007（権限を増やせない）、1204–1233（事前FD照会）、1336–1387（FD_READ）、1998–2134（PATH_OPENと継承rights）。`fd-table-v0.0.23.c` 349–379（BADFとNOTCAPABLEの区別）。本文SHAは `sources/retrieval.json`。
- 実環境のuvwasi 0.0.23ヘッダーも保存。BADF=8、NOENT=44、NOTCAPABLE=76、FD_READ=2、PATH_OPEN=8192を公式型と照合する。errnoのC定数と実呼出しの観測を同一視しない。
- [Node.js 25.2.1 WASI](https://nodejs.org/download/release/v25.2.1/docs/api/wasi.html) のpreview1・preopens・initializeを使用する。同版 `lib/wasi.js` 本文も保存。Security節はNodeが安全な隔離を保証しないと明記しているため、有限の拒否観測から一般的なアクセス防止を主張しない。
- 原典のmain/legacy取得2件は404。失敗を保持し、固定snapshot-01の別locatorを独立担当と確認して保存した。GitHub tree表示の取得失敗もあり、取得成功や未読本文を装わない。

本教材の4条件・ファイル6バイト・時間上限は独自の実験条件です。公式がこの実験を実行した証拠ではありません。

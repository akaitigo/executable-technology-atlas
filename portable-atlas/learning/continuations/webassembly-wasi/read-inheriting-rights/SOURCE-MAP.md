# Atlas：FD_READ と新しい FD の権限の根拠

この教材は前教材の保存済み公式資料を読みます。新しいネットワーク取得はしていません。本文のハッシュは `source-plan.json`、複製した固定 Wasm と検査器の由来は `source-provenance.json` にあります。

| 対応する問い | 固定版の原典と保存先 |
|---|---|
| 権限を減らすと、どの FD が変わるか | [uvwasi v0.0.23](https://github.com/nodejs/uvwasi/blob/v0.0.23/src/uvwasi.c#L967) 967–1007行。`../wasi-preopen-rights/sources/uvwasi-v0.0.23.c`。指定した FD の base と inheriting を更新し、権限の増加を拒否する。 |
| ファイルの読取りに必要な権限 | 同ファイル1358行。`fd_read` は対象ファイルの base に FD_READ があるか検査する。 |
| 新しいファイルを開くときの権限 | 同ファイル2047–2092行。ディレクトリの base に PATH_OPEN、新しく要求する権限が inheriting に含まれることを検査する。 |
| 開いたファイルにどの権限が保存されるか | 同ファイル2137–2147行。要求した base と inheriting を、そのファイルで可能な権限との共通部分として新しい FD に保存する。 |
| 権限不足と FD 不在の違い | `../wasi-preopen-rights/sources/fd-table-v0.0.23.c` 349–379行。今回の4条件は有効な preopen を用意するため、権限不足を比較する。FD 不在の BADF は前教材の対象。 |
| 型・権限ビット・返り値 | [公式 snapshot-01](https://github.com/WebAssembly/WASI/tree/snapshot-01/phases/snapshot/witx)。保存先 `snapshot-01-api.witx` と `snapshot-01-typenames.witx` は前教材の `sources/` 内。FD_READ=2、PATH_OPEN=8192、NOTCAPABLE=76。 |
| 安全な隔離として使えるか | [Node 25.2.1 Security](https://nodejs.org/download/release/v25.2.1/docs/api/wasi.html#security)。Node の WASI は安全なファイルシステム隔離を保証しない。 |

JavaScript の呼出し記録の引数は、教材の Wasm 関数へ渡す引数です。WASI の完全な引数列ではありません。固定引数、型、出力先は `module-contract.json` にあり、保存した610バイトを別方式で解読して照合します。例えば `open(3,128,8)` は内部で `path_open` の9引数を組み立て、ファイルの base に FD_READ=2、inheriting に0を要求します。

この4条件は、ディレクトリの inheriting を変えた後も、すでに開いたファイルの権限が同じであるという有限の比較です。一般的な権限取消し機構、他のランタイム、すべての WASI の機能を実証するものではありません。

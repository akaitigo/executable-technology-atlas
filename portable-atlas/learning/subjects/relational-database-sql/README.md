# SQL NULL・JOIN・制約の境界

Python標準ライブラリの`sqlite3`と`:memory:`データベースだけで、NULLの三値論理、INNER/LEFT JOIN、WHEREとONの行保持差、NOT NULL / UNIQUE / FOREIGN KEY拒否を観測する有限教材です。

## 再現

```bash
python3 observe.py
python3 verify.py
python3 -m http.server 8765 --bind 127.0.0.1
```

ブラウザで `http://127.0.0.1:8765/` を開きます。`observe.py`は`experiment.py`を新しいprocessで1回だけ実行し、全Oracleが通った候補だけを`evidence/`へdirectory renameでpublishします。失敗時は直前の成功Evidenceを残します。

## 実観測と説明の境界

- `evidence/raw-results.json`: 実際に発行したSQL、columns、raw rows、SQLiteのconstraint error。
- `evidence/run.json`: runtime identity、source digest、Oracle要約。
- `evidence/data.js`: 上記を画面へ運ぶ派生データ。ブラウザはSQLを再実行しません。
- `index.html` / `app.js`: 保存済み結果の説明モデル。画面操作は新たなdatabase observationではありません。

観測runtimeはPython 3.9.6から見えるSQLite 3.51.0です。PostgreSQLや他databaseで同じ結果になるとは主張しません。SQLite公式資料は本文を保存せず、`sources.json`にURL・locator・URL digestだけを保持します。

## 負例

`verify.py`は`= NULL`へ架空の行を追加、`IS NULL`の行を削除、LEFT JOINの保持行を追加/削除、foreign key無効化、constraint拒否の成功化、engineのPostgreSQL偽装、query削除を拒否します。

## Coverage

[COVERAGE.md](COVERAGE.md)を参照してください。このlessonは1 Subjectの有限入口であり、SQL全体またはrelational database subjectの完了証明ではありません。

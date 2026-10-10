# Coverage

| Surface | 状態 | Evidence / Gap |
|---|---|---|
| SQLite `= NULL` / `IS NULL` | observed | exact SQL + raw rows + truth values |
| SQLite INNER / LEFT JOIN | observed | 4 query variants + exact row order |
| WHERE filter / ON filter retention | observed | unmatched row disappears / remains |
| SQLite NOT NULL / UNIQUE / FOREIGN KEY | observed | actual `IntegrityError`; `PRAGMA foreign_keys=ON` |
| SQLite UNIQUE + multiple NULL | observed | two NULL rows retained |
| SQL全command / expression / function | unlearned | このfinite fixture外 |
| PostgreSQL / MySQL / SQL Server / other dialects | unlearned | runtime実行なし |
| Planner / index / statistics | unlearned | plan artifactなし |
| Transaction isolation / locks / concurrency | unlearned | concurrent runtimeなし |
| Schema migration / backup / recovery / operations | unlearned | 対象外 |

`observed`は`evidence/raw-results.json`と`verify.py`で閉じたrowだけを指します。残りをこの教材の成功から推論しません。

# 古い値で上書きしないためのKV

SQLite tableをbackendにした整数valueのversioned KVを作り、blind read→writeのlost updateと、`WHERE key + expected version`のconditional UPDATEを比較する有限教材。

実SQLite 3.51.0、Python stdlib `sqlite3`。各scenarioで2つの独立connection objectをnamed shared in-memory databaseへ接続し、autocommit statementを固定順序で交互に操作する。parallel thread、実locking、並列性能は未測定。shared-cacheの利用はこの有限fixtureのためで、運用推奨ではない。

## 再現

このmodule directoryで、既存原票を検査する。

```sh
python3 -B verify.py
python3 -B observe.py
```

どちらもread-only。新しい実観測で原票を更新する場合だけ明示optionを指定する。

```sh
python3 -B observe.py --write-evidence
python3 -m http.server 8767 --bind 127.0.0.1
```

`http://127.0.0.1:8767/`でcaseと最終valueの予想を選択し、「traceと答えを見る」、次/前のstep操作でSQL/rowcount/DB stateを読む。serverはCtrl-Cで終了。

## 実結果と境界

| Case | 実観測 |
|---|---|
| blind | A/Bが同じ0を読み、両方1を書く。2回成功でも最終1/version3 |
| CAS | A成功、Bのv1拒否。Bがv2を読み直し計算して最終2/version3 |
| type | str/bool/negative expectedversion、float/str/bool valueの6入力をAPIで拒否。更新SQLなし |
| unknown/stale | missing keyと古いversionはrowcount0。作成も既存変更もなし |
| ABA | value 0→5→0でもversion1→2→3。古いv1は拒否 |
| ABA reset | delete/recreateでversion1を再利用すると古いCASが通る。未保護の限界 |

通常APIはnonempty str key、signed 64-bit int value、0以上かつ最大signed int未満のint expected versionだけを受ける。boolをintへ暗黙変換しない。削除/再作成は境界実験のSQLで、通常CAS APIには追加していない。6型入力以外の全組合せまで試したとは主張しない。

## 原票と検証

- `kv.py`：型guardとconditional UPDATE。
- `experiment.py`：実connection/SQL操作。固定合成入力のみ。
- `evidence/stdout.json`：actual SQL/params/read rows/rowcount/state_after、6scenario。
- `evidence/run.json`：実時刻、Python/SQLite/source ID、入力、source digest。
- `evidence/artifacts.json`：原票/report/UI data/stderrのdigestとbytes。inventory自体は自己digestを持たない。
- `verify.py`：runner/APIをimportせず、独立状態機械で全stepを再計算。型拒否、未知key、ABAとreset限界、10改ざん負例、全source/artifact/UI bindingを検査。

更新は全candidateの検証後にdirectory renameでpublish。失敗時に既存成功原票を保持する。UIは保存データの再生で、クリック時にSQLiteを実行しない。diagramは論理状態の説明、物理lock/page/networkの実測ではない。

traceのSELECTではPython cursorの`rowcount=-1`をそのまま保存する。これは読取り件数ではない。読取り結果は`rows`、UPDATEの成否は0/1のrowcountから確認する。

一次資料locatorは`sources.json`、本文保存なし。画面確認は[QA.md](QA.md)、全Subject未教材は[COVERAGE.md](COVERAGE.md)、再利用入口は[Skill](skills/atlas-operational-data-stores/SKILL.md)。これはRedis製品・KV/cache/document/graph全体またはSubject完了の証明ではない。

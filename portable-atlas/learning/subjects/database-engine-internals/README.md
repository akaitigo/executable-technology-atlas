# 同じ答え、違う検索計画

問い：同じ表にindexを追加すると計画は変わるか。等価条件を式へ変えても同じindex検索が使われるか。

Python標準`sqlite3`の実`:memory:` connectionで256合成行を入れ、indexなしの`bucket = ?`、indexありの同じ条件、indexありの`bucket + 0 = ?`を比較する有限教材。観測SQLite 3.51.0ではSCAN / SEARCH / SCANとなり、結果は全条件で同じ16行。SCAN/SEARCHの名称から性能勝利や速度倍率は推論しない。

## 再現と操作

このdirectoryで実行する。

```sh
python3 observe.py
python3 verify.py
python3 -m http.server 8766 --bind 127.0.0.1
```

`http://127.0.0.1:8766/`を開き、3条件のボタンを選ぶ。SCAN/SEARCHを予想して「保存済み計画を見る」で答えを確認する。serverはCtrl-Cで終了する。

`observe.py`は新processを1回実行し、独立Oracle通過後だけEvidenceのdirectoryを切り替える。失敗は既存成功Evidenceを保持する。観測時刻は実行時刻。`experiment.py`のschema/index SQL、actual fixture、exact query、4列のraw plan、全result rowsを`evidence/stdout.json`へ保存。`run.json`にはPython/SQLite版・SQLite source ID・入力digestを保存する。画面は`data.js`で原票を再生し、ボタン操作時にSQLは発行しない。

独立Oracleはrunnerをimportせず整数集合から16行を計算し、multiset（欠落・重複）と順序を検査する。plan解釈は観測SQLite 3.51.0へ固定し、他版は再受入が必要。SQLite公式Docsもplan文字列形式の版依存を明記する。公式locatorは`sources.json`、第三者本文保存なし。

画面の経路図は説明模式図であり、物理B-tree、ページ配置、訪問数や時間の実測ではない。式はINTEGER固定fixtureで比較しており、あらゆる型・NULLへ同値を拡張しない。

## 検証と制限

`python3 verify.py`は結果改ざん・plan偽装・別index・式のSEARCH偽装・分母縮小・missing case・速度主張・版変更の9負例を拒否する。

[QA.md](QA.md)に実IAB受入、[COVERAGE.md](COVERAGE.md)に未教材、[skills/atlas-database-engine-internals/SKILL.md](skills/atlas-database-engine-internals/SKILL.md)にこのmoduleの再利用入口を記す。実time benchmark、ページ/WAL/crash recovery、他DB、planner全機能は未実施。この1教材はSubject全体の完成証明ではない。

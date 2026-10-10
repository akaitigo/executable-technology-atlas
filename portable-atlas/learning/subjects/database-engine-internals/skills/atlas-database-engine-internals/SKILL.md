---
name: atlas-database-engine-internals
description: このmoduleのSQLite実行計画教材で、index追加前後と等価条件・式条件の検索経路および結果同値を再現・説明する。ページ格納、WAL、crash recovery、他DBや速度ベンチマークの依頼には対応範囲を確認する。
---

# SQLite検索計画教材

このSkillの2階層上がmodule root。[README](../../README.md)と[Coverage](../../COVERAGE.md)で有限範囲を確認する。

- 記録を説明する依頼：`../../evidence/stdout.json`のactual SQL/plan/rowsと`../../evidence/run.json`のruntime/source digestを読む。原典は`../../sources.json`。
- 新しい観測を求められた場合：module rootで`python3 observe.py`、続けて`python3 verify.py`。Skill directoryからなら`python3 ../../observe.py`と`python3 ../../verify.py`。保存成功結果の更新を伴うため再実行の意図がある場合に使う。
- 可視化：`../../index.html`の予想・3条件・答えを使う。HTTP起動手順はREADME。画面は保存済み実SQLite観測の再生、図は説明模式図。
- SCAN/SEARCHだけで速度勝利を回答しない。plan文字列の判断は観測SQLite版へ限定し、他版の自動互換を主張しない。
- WAL/recovery/物理ページ/他DB/実時間性能など未教材の質問は、このmoduleでは未検証と答え、必要な実測を示す。Subject全体完成・PostgreSQL実行を推論しない。


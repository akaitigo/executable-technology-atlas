---
name: atlas-atomic-reload-snapshot
description: 合成JSONの有限reloadで一括snapshot採用・last-known-good・field混在を比較する。実OS設定、remote provider、分散reload、耐久性の操作には使わない。
---
README・contracts.json・expected-table.jsonを読み、route.pyの6入口へ依頼を対応づける。UIで予想→保存済み実験→候補/採用/拒否→tuple/版/trace→答えの順に辿る。
JSON parseとstrict型/範囲検証の後だけ採用する。正常版はfrozen dataclassを参照交換し、要求開始時に1snapshot採取。故障版は検証済み値をfield別に書く。候補v3の拒否時は採用v2と既存対照を保持する。実行失敗は正常答えにしない。
checker.pyと通常runner.pyはread-only。明示した再記録だけrunner.py --recordでfresh runを作る。UIはreaderでありreloadを再実行しない。予想だけの変更でも新値を保持し旧比較と答えを消す。
Python jsonの一次資料は読取/変換/構文エラーだけを支える。snapshot交換・last-known-goodは独自契約。Event gateの有限thread順序をOS/多process/分散atomicity保証へ一般化しない。
実OS設定、remote provider、分散reload、永続性・権限・公開・課金は未対応。READMEの次coverageへ案内し、このSkillから実操作許可を推定しない。

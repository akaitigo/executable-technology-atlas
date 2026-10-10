---
name: atlas-formal-methods-verification
description: 2 processのmutex有限モデルをPythonで全状態探索し、正常safetyとguard欠陥の最短反例を再現・説明するローカル教材。実mutexや任意protocolの検証には使わない。
---

# Mutexの状態探索教材

このSkillのdirectoryから`../..`が教材root。[README](../../README.md)で操作経路、[Coverage](../../COVERAGE.md)で仮定と未対応範囲を確認する。

- 再観測の依頼なら、教材rootで`python3 -B observe.py`、続けて`python3 -B verify.py`を実行する。標準Python 3.9以上だけを使う。
- 保存された結果の説明なら、[原票](../../evidence/run.json)と[生stdout](../../evidence/stdout.json)を読み、観測時刻・環境・実際のstate/transition数とcounterexampleを引用する。再実行していなければ現在の実観測とは呼ばない。
- [model.py](../../model.py)が状態・transition・invariant・BFS、[check.py](../../check.py)がchecker、[observe.py](../../observe.py)が新規process観測を保存する。
- [UI](../../index.html)の正常モデルでP0を入室、P1をwaitingに置く。次に欠陥モデルの最短反例を初期状態から進め、両者criticalの最初のstepを見る。[実traceの図](../../evidence/counterexample.svg)は保存した探索結果の再描画。

正常のsafety成立、意図的欠陥のsafety違反、checker subprocessの実行成功を分けて説明する。探索は有限domainの到達集合が閉じるまでで、深さ打切りはない。safetyからlivenessや実コードの正しさを推論しない。

TLA+/Lean証明、weak memory、任意process数、実OS lock、実装refinement、fairness付きtemporal model checkの依頼は、この教材では未対応と返し、その不足を具体的に述べる。依頼を受けただけで依存install・設定変更・外部公開へ拡張しない。

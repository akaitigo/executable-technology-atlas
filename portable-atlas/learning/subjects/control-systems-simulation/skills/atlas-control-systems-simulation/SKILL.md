---
name: atlas-control-systems-simulation
description: 一次遅れplantと比例feedbackのPython教材で、gain・Euler刻み幅・入力clipを比較する。実機調整、PID全機能やHILの検証には使わない。
---

# 一次遅れfeedback教材

このSkillの2階層上がmodule root。既存の[使い方・モデル境界](../../README.md)を読み、依頼をこの1モデルに限定する。旧Atlas/Core/Definitive作業や他Subjectへ拡張しない。

- 数値比較は既存[runner](../../simulator.py)の`simulate(gain, dt, steps, limit)`を再利用する。必要な条件だけ標準Pythonで計算し、入力と結果を明示する。CLIの`python3 simulator.py --record`は5 presetの原票を置換するため、既存原票を守る必要があればrecordなしで実行する。
- checkerは`python3 -m unittest -v test_simulator`。[検査コード](../../test_simulator.py)、[CLI原票](../../observations/presets.json)、[実画面QA](../../QA.md)を参照できる。
- 図・操作UIは[entry](../../index.html)。`python3 serve.py`をmodule rootで起動しloopback port 18771で開く。停止はCtrl-C。UI計算もPython APIを呼び、固有JSONに結果を保存する。Docker・実機接続は不要。
- Eulerの離散Oracle一致と、連続時間解の近似誤差を区別する。clip時に線形aを非線形系の安定性判定へ流用しない。任意clipでOracle未適用ならそのまま伝える。
- 正常な依頼例：「K=2でh=0.1と0.8を比較」→既存runnerで計算し、a=0.7と−1.4、数値発散と連続モデル安定を分けて説明する。
- 境界例：「このgainを実モーターへ設定して安全性を保証」→未対応と返す。実機、PID全機能、HIL、安全認証の証拠はない。新しい接続・設定・他repository作業を行わない。

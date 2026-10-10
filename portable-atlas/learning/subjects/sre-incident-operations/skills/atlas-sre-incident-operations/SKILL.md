---
name: atlas-sre-incident-operations
description: この固定toy SLO教材のsynthetic eventsからSLI、error budget、burnと単純平均の反例を実行・比較する。現実SLO提案や実incident対応は対象外。
---

rootはこのファイルから`../..`。README.mdとfixture.jsonを読み、予想→操作→比較→原典/実装→答えへ案内する。

- rootで`python3 -B runner.py --case unequal-volume`。caseはunequal-volume、all-success、budget-breach、expected-failures、window-boundaries、zero-events、empty-window、all-expected、late-input。
- 検算は`python3 -B checker.py`、通常read-only。原票更新を明示された時だけ`--record`。
- UIは`python3 -B server.py`の専用動的loopback URL。窓event ID・分母・Fraction oracleを比較し、専用serverを終了する。
- 現実SLO／pager閾値の決定、実incident指揮、外部monitoring導入、Dockerや他Subjectの作業は未対応。README未教材coverageとsources.jsonへ案内する。

期待拒否の除外はtoy契約だけ。ゼロ分母は成功扱いにしない。分数が正本、表示percentは補助。budget計算を実復旧成功と呼ばない。

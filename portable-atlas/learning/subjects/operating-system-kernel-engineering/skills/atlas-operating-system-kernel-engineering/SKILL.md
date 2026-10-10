---
name: atlas-operating-system-kernel-engineering
description: この有限pipe EOF教材の実child・FD leak・bounded timeout・signal cleanupを既存runner/checker/FD図UIへrouteする。kernel改造、VM、host設定、外部PID操作には使わない。
---

rootは`../..`。[README](../../README.md)で入力とownership、[coverage](../../COVERAGE.md)で次の4実験、[原典](../../SOURCES.md)で規格/API bindingを確認する。

- `python3 -B route.py pipe|verify|fd-diagram|sources`は既存runner.py/checker.py/index.html/SOURCES.mdへrouteする。
- `python3 -B runner.py`またはREADMEの`--input-json`は実owned child/pipeを一時操作するが原票を書かない。外部PIDを引数にしない。拒否exit2はchildなし、空payloadの正常EOFとは区別。
- `python3 -B checker.py`は通常read-onlyで保存原票・独立lifecycle oracle・digest・local linksを検査。原票再観測の明示依頼にだけ`python3 -B observe.py --write-evidence`。binding更新の明示依頼にだけ`python3 -B checker.py --seal-evidence`。hash更新を再実行と呼ばない。
- [UI](../../index.html)は予想→event replay→FD/PID/table oracle比較→原典/実装→答え。previewはdynamic loopback一時serverを使い、専用processを終了する。
- [raw](../../evidence/raw.json)/[run](../../evidence/run.json)の実時刻と環境を述べる。monotonicは各process内だけ。SIGTERM cleanupを正常EOF完了と呼ばない。timeoutを無限blockやscheduler性能の証明と呼ばない。

kernel-patch、vm、scheduler、memory、filesystem、driverや任意の未定義topicはunsupported/exit2で[coverage](../../COVERAGE.md)へ。install/OS設定/外部process操作/新権限/公開へ拡張せず、未教材の具体的な問いを案内する。

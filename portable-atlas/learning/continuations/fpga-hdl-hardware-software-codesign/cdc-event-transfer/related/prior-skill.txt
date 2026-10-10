---
name: atlas-fpga-hdl-hardware-software-codesign
description: この有限2bit counter教材の同期reset・enable・nonblocking next-state誤用を既存runner/checker/波形UIへ案内する。合成、timing closure、CDC、AXI/HLSや実機検証の実施には使わない。
---

教材rootは`../..`。[README](../../README.md)の契約、[coverage](../../COVERAGE.md)の次の4実験、[sources](../../SOURCES.md)を入口にする。

- `python3 -B route.py counter|verify|waveform|sources`で既存`runner.py|checker.py|index.html|SOURCES.md`へrouteする。独自runnerや外部工具を増やさない。
- counterは`python3 -B runner.py`、customはREADMEの`--input-json`。通常read-only。input拒否exit2と空traceの正常を区別する。
- 検証は`python3 -B checker.py`。原票は更新しない。原票の再観測が明示依頼された場合だけ`python3 -B observe.py --write-evidence`、bindingを更新する明示依頼には`python3 -B checker.py --seal-evidence`。hash更新を新しい実行証拠と呼ばない。
- 波形は[UI](../../index.html)の予想→event操作→3variant/oracle比較→原典/実装→答え。previewは`python3 -B preview.py`でdynamic loopbackに限定し、専用processだけを終了する。
- 保存観測は[run](../../evidence/run.json)と[raw](../../evidence/raw.json)。iverilog/verilatorなしのPythonモデル実行をRTLツール実行・合成・物理timing・実機の証明と呼ばない。

`synthesis`, `timing`, `cdc`, `axi`, `hls`, `hardware`や未定義topicは`route.py`でunsupported/exit2となる。[coverage](../../COVERAGE.md)の未教材の問いと公式locatorへ案内する。syncとasyncは別のreset契約。asyncの論理応答は安全なreset解除の証明ではない。global install、依存追加、課金、公開、OS/GitHub設定の操作へ拡張しない。

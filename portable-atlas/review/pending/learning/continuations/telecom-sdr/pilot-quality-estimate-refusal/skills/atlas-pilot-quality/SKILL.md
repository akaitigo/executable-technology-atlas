---
name: atlas-pilot-quality
description: この教材の合成pilot I/Qから複素gainを推定し、magnitude二乗と正規化residualの品質gate、拒否、通過誤りを検証する。実RFやMAP/規格検証には使わない。
---

2階層上の教材rootで[契約](../../EXPECTATIONS.md)を読む。h2とNRの等値を含む独自gate、NR分母=received pilot energyを保持する。Ek0/h0で逆数を作らない。拒否は復調なし、harness BERnull/比較0bit。期待拒否を成功受信へ数えない。

receiverへtruthを渡さず、harnessだけでpayloadを答合せする。整合逆位相pilotがNR0でgateを通過して全bitを誤る反例を残す。低residualから正しい位相/無誤りを推定しない。oracleの成分normal equations/energy identityをproducerのcomplex helperへ統合しない。

`python3 -B runner.py`、`python3 -B test_negative.py`、`python3 -B checker.py`を実行する。通常modeはread-only、新原票は明示--record。UI変更時は予想→scale/noise/閾値→採否/IQ/復調表→原典/実装→答えを実ブラウザで確認。編集失効、保留古い結果、503も検査する。

[根拠](../../SOURCES.md)と[範囲](../../COVERAGE.md)を読み、MIT所定gate/MAP、RF/規格/機器性能、確率BER一般へ拡張しない。Skillから公開、global install、権限の許可を推定しない。

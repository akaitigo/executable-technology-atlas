---
name: atlas-histogram-resolution
description: 固定区間へまとめた件数と、元の分位点・所属区間・独自補間値を区別するAtlasの有限教材。
---

# Atlas — 集約後の分位点を読み解く

[README](README.md) → [契約](CONTRACT.md) → [画面](index.html) → [原典と実装の対応](SOURCES.md) の順に読む。[手計算表](expected.json) は予想であり、実行記録の代わりにしない。[保存した計算結果](observations/run-01/results.json) と [実行時の集約実装](observations/run-01/inputs/histogram.py) を参照する。cases[].id と results[].q で以下の例に対応する。

1. **同じ棒グラフなら p50 も同じか。** pair-a と pair-b の q=1/2 を比較する。件数と集約側の入力が同じでも、生データ側の値は2と9。集約値から片方を識別できない。[前提の nearest-rank](related.html?doc=collector) に戻り、欠落の問題とは区別する。
2. **推定15msは実際に15msを観測したということか。** pair-a/pair-b の q=3/4 を使う。補間は同じ15でも、元の値は11と18。誤差は補間−元の値なので一方は正、他方は負。finer-a は今回の区間が狭まる対照であり、普遍的な精度保証にはしない。
3. **空・端点・製品の質問にはどう答えるか。** empty は区間も値も null。pair-a の q=0,1 は補間0,20と生データ1,12を区別する。実 collector、Prometheus 適合、sketch、SLO運用を求められたら [未対応範囲](COVERAGE.md) を示す。

3例は保存計算と前提・実装へ辿って確認し、readerでは20組の実DOMと資料導線を別に確認した。Skill3例の読取利用と全20組の画面検査を同じ評価とはしない。これは限定的な利用確認であり、一般Agent評価や未知の質問への保証ではない。既存教材・共有元を編集せず、再計算や新サービスの起動を回答のために追加しない。

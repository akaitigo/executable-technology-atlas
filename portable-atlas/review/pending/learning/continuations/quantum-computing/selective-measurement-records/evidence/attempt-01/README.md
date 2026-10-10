# 測定結果の記録を保持するか、捨てるか

1qubit Z射影のσk、pk、正規化したconditional densityを分け、記録を捨てたweighted ensembleを別に追う。pk=0は到達不能branchでconditional=null。正しい測定全体が不正になるわけではない。

biased入力のpは9/25・16/25。H後ensembleの対角は1/2、非対角は−7/50。等重み化の故障は非対角を0に変えるが最終Z確率は同じ1/2ずつで、確率だけでは見逃す。正規化漏れ、等重み化、確率0を無理に割る別faultを比較する。

このディレクトリで:

```sh
python3 -B runner.py
python3 -B test_negative.py
python3 -B checker.py
python3 -B server.py --port 0
```

serverのURLを開き、確率・trace・H後densityを予想し、条件とrecordを選んで比較する。record0/1は条件付きbranchの説明用指定、実際に得たshotではない。σ→pk→conditional→H後、記録破棄のweighted/直接map→H後、fault全行列を辿ってから答えを読む。JSON上書きのcomplex成分は文字列pair[real,imag]、例えば["1/2","0"]。record0/1だけはJSON整数、boolは契約外。

通常CLIはread-only、原票更新だけrunner/checker/test_negativeの明示 `--record`。currentは合格rawだけへ昇格。実subprocess、別processの成分閉式oracle、手literal、source SHA、UI receiptを照合する。HはRρR/2でexactに計算し、√2をfloat化しない。

[契約](EXPECTATIONS.md)、[原典](SOURCES.md)、[範囲](COVERAGE.md)、[Skill](skills/atlas-selective-measurement/SKILL.md)、[QA](QA.md)。quantum-computing LEARNING_PATH §6実験2の独立continuation候補。既存D/2qubit Bellのruntimeは使わない。PRNG、実機shot/実測定record、一般POVM、量子優位性は未実証。Subject/Atlas完成やaccepted数は主張せず、公開・commit・push・global installは実施していない。

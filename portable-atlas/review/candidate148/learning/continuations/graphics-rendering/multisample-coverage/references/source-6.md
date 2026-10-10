# 近面clipをperspective divide前に行う

1頂点が近面外の三角形はclipで四角形になり、再三角形化が必要になる。手計算例の面積はnear_clip=3/8、no_clip=1/2、外頂点を捨てるだけ=0。交点のwも保持してからx/w,y/w,z/wを求める。

graphics-rendering LEARNING_PATH §6実験1の独立continuation候補。Subject/Atlasのcompleteは主張しない。Python標準Fractionの有限CPUモデル。D3D/GPU/driver、全6平面、実float、属性補間、pixel coverage、depth testは未実証。side/far外とw<=0は拒否する。

このディレクトリで実行する:

```sh
python3 -B runner.py
python3 -B test_negative.py
python3 -B checker.py
python3 -B server.py --port 0
```

serverの表示したURLを開き、交点・面積を予想して「clipとdivideを比較」。3方式の図、同次交点、NDC、fan面積を読んでから答えを開く。条件JSONで頂点を変更する。各入力変更で図・答え・rawを消す。保留後の変更は古い結果を無視する。503、producer故障、入力拒否を区別する。

通常コマンドは記録を書き換えない。明示記録はrunner/checkerの `--record`。currentは合格原票だけを指す。実subprocessのstdin/stdout/exit、別process oracle、source SHA、UI receiptを照合。手literalと独立oracleはproducer未作成時に固定した記録がある。図は説明表示、native captureは実ブラウザ観測。

[契約](EXPECTATIONS.md)、[根拠](SOURCES.md)、[範囲](COVERAGE.md)、[Skill](skills/atlas-near-plane-clip/SKILL.md)、[QA](QA.md)を参照。Skillはこの単位だけで利用し、global installしない。公開・commit・pushは実施していない。

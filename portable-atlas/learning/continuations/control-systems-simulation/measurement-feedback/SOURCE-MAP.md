# Atlas — 既存前提と一次資料への対応

[前提への実在リンク](PREREQUISITES.md)から元の学習順へ戻れる。目標は task-8/atlas-97-field-goals-ja.md:1033–1043 の89。全体件数ではなく、元学習経路の実験3を今回の問いの根拠にする。

既存の根拠は、制御subject README:27–31,59、LEARNING_PATH:50,62、solver-versus-sampled-control README:5–25,40、pi-saturation-windup README:15–19/COVERAGE:5、observation-delay-braking-distance README:15–25、measurement-bias-repeatability README:7–19、control-noise-robustness-confirmation README:7–18,42である。最後の2つは統計的な固定表、今回の動的帰還とは範囲を分ける。

## 本文を読んだ資料と使う範囲

- [MIT 6.302 Recitation 1: Closed-loop vs. Open-loop Systems](https://www.mit.edu/~6.302/notes/6.302rec1.pdf)、PDF p.1とp.5。出力を測って入力を変えること、異なる時刻を比較する遅延の論点を読む。2026-10-06に本文取得成功。今回の係数・雑音列・量子化法を定めた資料ではない。
- [SciPy StateSpace](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.StateSpace.html)、取得時表示1.18.0、冒頭の離散状態式 x[k+1]=Ax[k]+Bu[k]。2026-10-06に本文取得成功。表記の入口として参照するだけで、SciPyをインストール/実行していない。
- [MathWorks Quantizer](https://www.mathworks.com/help/simulink/slref/quantizer.html)、取得時表示R2026b、DescriptionとQuantization interval。量子化を所定の間隔に写す観点を読む。2026-10-06に本文取得成功。今回の正負half-away規約は契約へ明記し、製品の型や境界仕様の互換試験とはしない。

CaltechのFeedback Systems chapter 12 PDF（fbs-loopsyn_24Jul2020.pdf）は検索結果に測定雑音の説明が出たが、本文openはtimeoutになった。本文確認済みの根拠にはせず、連続再取得はしていない。取得結果はsources.jsonへ残す。

各本文は正式web読取の結果で、PDF/HTMLの元byteを保存していない。本文hash取得済みとは記載しない。実装前のfixture/手表と資料locatorを別に固定する。固定雑音、量子化の境界、入力保持に対応する係数1/2、6更新と終端の扱いは独自の有限契約である。

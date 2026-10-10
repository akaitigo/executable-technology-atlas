# Atlas：呼ぶ前の型検査と、呼ばない関数の値

この教材の問いは「実行時に関数という値が得られるのに、なぜ型検査では拒否されるのか」です。Intと関数型だけの小言語で、型の判断に使うΓと、実際に評価した結果を見比べます。

まず [現在の確認状態](status.json) を読み、[画面](index.html) → [前提](PREREQUISITES.md) → [原典と実装の対応](reference.html) → [限定Skill](SKILL.md) と進んでください。画面は保存した結果を読むものです。結果の閲覧に新しい計算は要りません。測定がまだないときは契約と手期待までを案内します。

予想するのは、型付けの受理・拒否と、通常経路の評価呼出数です。関数の本体を型検査することは、その本体を実行することではありません。拒否した3条件では通常経路の評価は0回。診断比較では注釈だけを消して固定評価器を別に呼び、stuckまたはFn valueを学習用に観察します。この2経路を一つの成功にまとめません。

| 条件 | 型判断 | 診断の手期待 |
|---|---|---|
| 関数を値として置く | Int→Int | Fn value / 0歩 |
| 関数を引数に渡す | Int | 3 / 3歩 |
| 整数を呼ぶ | 関数位置で拒否 | stuck / 0歩 |
| 関数に整数を足す | Add左で拒否 | stuck / 0歩 |
| 未呼出関数の本体が整数を呼ぶ | 本体内で拒否 | Fn value / 0歩 |

[契約](CONTRACT.md)、[入力AST](inputs/cases.json)、[実装前の手期待](expected.json)、[手で追う例](HAND_TRACE.md) を順に参照できます。最新の測定や受入を手期待そのものと取り違えないよう、状態記録から保存した実行ログへ進んでください。

入力上限は64項node/深さ16、整数literal±1000、型の深さ4、評価予算0..16です。固定5条件は予算8。Intのbool混同を拒否します。入力形式拒否、静的型拒否、診断stuck、予算切れ、実process失敗は別の状態です。

再現時は [実行条件](RUN_CONDITIONS.md) を確認し、新しい保存先へ記録します。既存Python標準ライブラリだけで、資源・優先度・時間・所有子の回収を確認します。具体的な実行コマンドと採用結果は以下の案内へ結びます。教材を開くだけでproducerを再実行しません。

今回は型注釈から式の型を合成します。注釈なしの引数型推論、単一化、多相型推論、型安全性の一般証明、全入力のprogress/preservation、未実行枝の保証を含みません。前提の既存実行例と今回の型判断の増分は [COVERAGE](COVERAGE.md) へ。元repo未統合、一般Agent評価とは別です。

## 保存結果の確認と再現

教材ディレクトリで `python3 -B verify.py observations/attempt-20261007T000929746801Z/run.json --mutations` を使うと、既存の保存値を読み、型checkerや評価器を再実行せず照合できます。この確認は保存値の読取で、対象の再計算ではありません。

新しく計算する場合は、新しい所有参照と今回限りのidentity判断を用意し、他の対象処理と重ならない枠を確保します。`resources.py --root-slot` の文面だけで許可が生じるわけではありません。

```sh
python3 -B resources.py --root-slot '今回の単独枠・GUI idle・他target 0の判断' --gui-idle --other-targets-zero --decision /absolute/path/current-decision.json --execute-slot
python3 -B run.py --execute --resource-record records/resources-今回の観測.json
```

freshは60秒以内、全条件成立時だけ1回です。不成立なら開始せず記録を残します。上記の記号的pathは実在の今回記録へ置き換えます。閲覧用HTTPは教材ディレクトリを起点とする静的配信で足り、GUI検査は提供されたpageだけを操作します。画面検査コード自身はbrowser/context/tab/serverを作りません。Markdownがdownloadになる配信では可視本文とは別にbytes/hashを確認します。

初回の実測は [MEASUREMENTS](MEASUREMENTS.md) と [保存した実行ログ](observations/attempt-20261007T000929746801Z/run.json) にある。型受理2/拒否3、通常評価2回/別診断5回を分けて読む。現在の実画面・独立受入は状態記録を参照する。

## 画面を開く

既にこの教材を配信しているloopback URLがあれば、その `/index.html` を開きます。単体利用ではこのディレクトリを作業位置にして、次の標準HTTP配信を使えます。割り当てられたport番号を起動ログで読み、同じhostの `/index.html` を開いてください。ファイル直接起動は今回の画面受入範囲ではありません。

```sh
python3 -m http.server --bind 127.0.0.1 0
```

配信を開始するのはこのコマンドを明示的に使ったときだけです。自分で開始した配信はCtrl-Cで終了します。今回の画面確認はroot管理の既存pageと教材配信を使い、作者がbrowser/serverを起動したものではありません。[限定Skillの通常手順](SKILL.md) はstatusから保存した証拠を読むための案内です。

# 条件付き確率・Bayes・base-rate

Catalog ID: `mathematical-statistical-foundations`。既知の合成有限populationを2×2表へ分け、1要素を等確率に選ぶ場合の確率を計算する教材です。標準Pythonだけで正確Fractionを算出し、画面で条件となる集合を変えます。個々の要素は中立なclass A/Bとtest+/test−のラベルだけを持ちます。

## 予想 → 操作

「Aの90%がtest+なら、test+の90%はAだろうか？」と予想してください。Aが1%の例と50%の例では感度・偽陽性率が同じです。priorだけが違う場合、PPVが同じになるかも予想します。

このdirectoryで起動します。新しい依存関係はありません。

```bash
/usr/bin/python3 -B lesson.py --port 18747
```

`http://127.0.0.1:18747`をブラウザで開き、合成population、予想、4つのcountsを設定して「Pythonで数えて比較」を押します。「Aだけを見る」と「test+だけを見る」を切り替え、図の濃い点と分母を照合してください。固定比較のbarは現在入力とは独立に、Aが1%と50%の2例を並べています。終了時は起動ターミナルで`Ctrl-C`。

入力は`ap`=A∩test+、`an`=A∩test−、`bp`=B∩test+、`bn`=B∩test−。各cellは0〜2000の整数、全体合計1〜2000。JSONのbool・小数・文字列はcountsとして拒否します。UIでも負数・小数を拒否します。空の条件集合は有効な入力ですが、その条件付き確率は未定義です。全populationが空の入力自体は拒否します。

## 正常 / 境界の実測

Mac標準CPython 3.9.6、macOS 26.1 arm64、`fractions.Fraction`。CLI原票の観測時刻は2026-10-05 13:48 JST、HTTPとIABの個別観測時刻は各原票にあります。サンプリングや乱数は使っていません。

| population | A+ / A− / B+ / B− | prior P(A) | 感度 P(test+\|A) | 偽陽性率 P(test+\|B) | PPV P(A\|test+) |
|---|---|---|---|---|---|
| Aが1% | 9 / 1 / 99 / 891 | 1/100 | 9/10 | 1/10 | 1/12 |
| Aが50% | 450 / 50 / 50 / 450 | 1/2 | 9/10 | 1/10 | 9/10 |
| Aが10% | 90 / 10 / 90 / 810 | 1/10 | 9/10 | 1/10 | 1/2 |
| test+なし | 0 / 10 / 0 / 990 | 1/100 | 0 | 0 | 未定義 |
| Aなし | 0 / 0 / 100 / 900 | 0 | 未定義 | 1/10 | 0 |
| Bなし | 90 / 10 / 0 / 0 | 1 | 9/10 | 未定義 | 1 |
| 手数え12要素 | 2 / 1 / 3 / 6 | 1/4 | 2/3 | 1/3 | 2/5 |

![Aが1%・test+条件の実画面](media/rare-positive.jpg)

Aが1%の例では、感度はA集合の9/10、PPVはtest+集合の9/108=`1/12`です。同じ9要素を分子にしても分母が変わります。Aが50%の例では感度とPPVがどちらも9/10ですが、この一致から一般に条件を逆転できるとは結論できません。

![test+が空の実画面](media/zero-denominator.jpg)

test+が空なら`P(A|test+)`は未定義です。Aが空でtest+が100要素ある別例では、感度が未定義でもPPVは0です。未定義と確率0を区別します。

## 原典 / 実装 → 答え

参照はH. Pishro-Nik著 *Introduction to Probability, Statistics, and Random Processes*（2014）の[著者公開教材 §1.4.0](https://www.probabilitycourse.com/chapter1/1_4_0_conditional_probability.php)と[§1.4.3 Bayesの規則](https://www.probabilitycourse.com/chapter1/1_4_3_bayes_rule.php)。2026-10-05に定義と公式を確認しました。歴史的な1763年論文の直接取得はHTTP 403で確認できず、この教材の根拠には使っていません。第三者本文は保存していません。

条件付き確率は`P(A|T)=P(A∩T)/P(T)`、ただし`P(T)>0`。A/Bがpartitionを作り、両classが非空なら、Bayesは次です。

```text
P(A | test+) = sensitivity × prior
              / (sensitivity × prior + false_positive_rate × (1 − prior))
```

この教材のpriorは既知populationのAの割合です。未知の母数についての主観的priorやposterior推定は扱いません。条件の逆転にはpriorとtest+の総確率が必要です。[Python Fraction仕様](https://docs.python.org/3.9/library/fractions.html)は整数比から正確な有理数を作る入口です。実行版は3.9.6、参照した3.9系文書の表示版は3.9.25です。

[lesson.py](lesson.py)の`calculate`は2×2 countsから条件ごとの分子・分母を出します。別の`enumeration_oracle`は全要素を `(class, test)` として列挙し、集合で選別して数えます。Bayes oracleは正確なjoint massの比と重み付き条件確率を照合します。空classのjoint massは0ですが、そのclassを条件とする確率そのものは未定義のままです。

[test_lesson.py](test_lesson.py)では、production countsとは別に手書きした12ラベルを数え、`prior=1/4`、感度`2/3`、偽陽性率`1/3`、PPV`2/5`の既知Fractionへ照合します。追加の小さな255非空tableでもoracle整合を検査しました。列挙oracleは計算経路を分けた検査であり、入力countsが現実に正しいことを保証する外部データではありません。

答え: `P(test+|A)`と`P(A|test+)`は違う条件を持つ確率です。感度・偽陽性率が同じでも、known populationのA/B構成が変わればPPVは変わります。分子・分母・条件を明示して数えると、この違いを確認できます。

## 再現・原票

```bash
# 読み取り専用: 保存済みsource/結果/画像binding検査 + 8件のunittest
/usr/bin/python3 -B verify.py

# 同じ8件のテストを単独で実行
/usr/bin/python3 -B -m unittest -v test_lesson

# 明示的な原票更新（指定ファイルを書き換える）
/usr/bin/python3 -B lesson.py --record
/usr/bin/python3 -B verify.py --record-checks

# serverを別ターミナルで起動済みの場合、6 HTTP原票を更新
/usr/bin/python3 -B verify.py --record-http
```

- [python.json](observations/python.json): 7つの正常/境界case、7拒否入力、実行環境/時刻、raw counts、source hash、全Fraction。
- [stdout.txt](observations/stdout.txt): `lesson.py --record`が実際にprintしたJSON lineそのもの。
- [tests.txt](observations/tests.txt): 8件の実unittest出力。
- [http.json](observations/http.json): 6 HTTP statusと応答bodyそのもの。正常、prior変更、分母0、負counts、全体0、手数え例への回復。
- [ui-dom.json](observations/ui-dom.json): 背景IABの8状態のDOM原票と個別時刻。条件A/test+、prior変更、分母0、Aなし、負counts、全体0、回復。
- [media.json](observations/media.json): 5枚の実JPEG、寸法/digest、source/DOM binding。全ページ静止画。図はPython結果を描画する説明用配置で、操作動画ではありません。

日本語、counts、分子/分母、Fraction、条件外の淡色点、比較bar、未定義/拒否/回復を実画面で目視確認しました。IAB engineの版は今回のAPIでは取得していません。スマートフォン寸法とassistive technologyでの操作QAは未実施です。検査の通常実行は原票やtests.txtを書き換えません。新しい観測の更新は上記の`--record*`だけで行います。

## 説明モデル / 未教材Coverage

| 分野 | この教材の範囲 / 未対応 |
|---|---|
| 有限集合確率 | 全population既知・等確率の1要素選択、A/Bの2分割、testの2分割 |
| Bayes / base-rate | counts・列挙・joint/weighted Fractionの照合。samplingなし |
| 図と百分率 | 1点1要素。barは各集合の分母へ正規化。図の座標と百分率は近似 |
| 推測統計 | 未教材: 母数推定、信頼区間、仮説検定、sampling bias、未知prior |
| 連続分布 | 未教材: 密度、積分、連続条件付き分布、測度論的な条件付け |
| 線形代数 | 未教材: ベクトル、行列、固有値、分解 |
| 最適化 | 未教材: 勾配、凸性、数値最適化、最適decision threshold |
| 因果 / 現実の判断 | 未教材: 因果推論、実データの率検証、医療など個別判断 |
| 知識・理解度 | 利用者の理解度や分野全体の完成を測定していない |

## 限定Skill

[atlas-mathematical-statistical-foundations](skills/atlas-mathematical-statistical-foundations/SKILL.md)はこのmoduleの実装、checker、図、原票を使う入口です。`skill-creator`のscope保持・簡潔なdiscovery方針を使い、global installや新しいrunnerを追加していません。frontmatter/namingは`quick_validate.py`で検査し、正常・分母0・未対応のroutingを[local確認記録](observations/skill-review.md)へ残しています。独立Agent評価や全Subject Skillの完成は示していません。

教材専用directoryのみを作成・検証しました。Portal共通文書、既存Subject、Core/Graph、Git設定は変更していません。公開・commit・pushは行っていません。

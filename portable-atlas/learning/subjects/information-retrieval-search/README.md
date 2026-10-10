# 転置indexと更新の境界

Python標準ライブラリだけで、5件の合成documentを転置index化する有限1教材です。AND/ORの13 queryを実行し、独立full scanと比較します。rankingや検索分野全体の完成を扱う教材ではありません。

初期状態ではAND `blue green`がd1、ORがd1/d2/d3/d4。d1を`Blue green note`から`Gold green note`へ変更し、indexを更新しないと、削除したblueで余分なhit、追加したgoldでmissing hitが発生します。rebuild後はどちらもfull scanと一致します。

## 学習の道筋

前提は集合の共通部分/和集合と、document ID・本文を分けて考えることです。Python未経験でも画面で集合stepを読めます。実装を追う場合はdict/setと関数呼出しが必要です。

1. **仕組み**：本文→token→term別posting→AND/OR結果を、`indexer.py`と画面のstepで追う。
2. **正常と異常**：初期AND/OR→d1の更新（indexは古い）→stale/missing→rebuildの順に操作する。`verify.py`は現在本文の独立full scanで比較する。
3. **実務判断**：検索結果がおかしい時、本文・queryのtokenとindex入力の世代を分けて調べる。この実験ではindex再構築が不一致を解消する。ただし実製品のrefresh/commitや整合性設定の選択は未検証。ORはANDより広い集合であって「関連性が高い」意味ではない。
4. **限界と原典**：ASCII限定・空query設計・ランキングなしを確認してから、[Boolean retrieval](https://nlp.stanford.edu/IR-book/html/htmledition/boolean-retrieval-1.html)と[query processing](https://nlp.stanford.edu/IR-book/html/htmledition/processing-boolean-queries-1.html)へ戻る。

### 次に学ぶ問いと実験（すべて未実施）

| 主要未教材概念 | 次の有限実験案 / 判断したい問い | 著者原典locator |
| --- | --- | --- |
| 言語別tokenization、normalization、phrase | `C++`・hyphen・日本語を同じ本文/queryへ入れ、tokenizer変更でhit集合がどう変わるか比較。語順を無視するANDでphraseを代用できるかは別に検証する。 | [Tokenization](https://nlp.stanford.edu/IR-book/html/htmledition/tokenization-1.html)、文字分割と言語別の境界 |
| 動的index、削除、整合性 | 追加/削除/更新を途中で止めた増分indexとfull rebuildをfull scanで照合。いつ検索可能になり、失敗時どの世代を読むか？ | [Dynamic indexing](https://nlp.stanford.edu/IR-book/html/htmledition/dynamic-indexing-1.html)、auxiliary indexと削除管理 |
| relevance、TF/IDF、BM25 | term頻度とdocument長だけを変えた合成corpusで、Booleanの同一hit集合とscore順位の違いを計算。検索できることと上位が有用であることを分離する。 | [Okapi BM25](https://nlp.stanford.edu/IR-book/html/htmledition/okapi-bm25-a-non-binary-model-1.html)、term frequency / document length |
| 検索品質評価 | 人が定めた小さな関連document集合でAND/ORのprecision/recallを比較。full scan一致という実装検査だけで利用者の関連性を保証できるか？ | [Evaluation of unranked retrieval sets](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html)、precision / recall |

製品engineの永続化/障害回復/アクセス制御/分散検索/性能容量、semantic embeddingは上記4本を行っても別途未教材です。導入判断には製品別の公式仕様と実runtime検証が必要で、この原票から推定しません。リンクは2026-10-05に確認した著者教科書の該当節で、本文は保存していません。

## 再現

このdirectoryで実行します。Python 3.9以降・標準ライブラリのみ。既定の2 commandは保存済み原票を読むだけです。

```sh
python3 -B verify.py
python3 -B observe.py
```

実行原票を更新する場合だけ、明示optionを使います。

```sh
python3 -B observe.py --write-evidence
```

実行と独立Oracleが成功した候補だけをdirectory renameで公開し、swap失敗時は直前成功原票を復元します。実行時刻は実測で、runtime/input/source digestは`evidence/run.json`、実postings・query・result rowsは`evidence/stdout.json`、Artifact digest/bytesは`evidence/artifacts.json`です。Oracleはindexerをimportせず、regexでもなく文字単位にtokenを抽出して全documentを走査します。10件の改ざん負例を拒否します。

## 画面

```sh
python3 -m http.server 0 --bind 127.0.0.1
```

表示された自分のportをブラウザで開きます。他担当のport/serverを停止しないでください。画面は保存済み結果の再生で、新しいqueryを実行するものではありません。queryを選択→一致/余分/missingを予想→postingと答えを見る→stepで集合演算→原典・実装へ戻る順に使います。終了はこのserverのterminalでCtrl-C。

## 境界

tokenizerは小文字化とASCII `[a-z0-9]+`。空queryは全件ではなく0件、未知termは空posting、重複termは一度だけ参照します。これらは本教材の明示設計であり、製品engine共通の仕様ではありません。set演算を使うため原典のsorted-list merge実装や性能を証明しません。

[一次資料locator](sources.json)、[coverage](COVERAGE.md)、[画面・検証QA](QA.md)、[教材専用Skill](skills/atlas-information-retrieval-search/SKILL.md)を参照してください。第三者本文・画像は保存しません。

# Atlas：原典と既存の不足への対応

| 根拠 | locator | この教材で使う範囲 |
|---|---|---|
| 97分野目標 | task-8/atlas-97-field-goals-ja.md:785–795、目標67 | 集合一致と順位を区別し、手計算で照合する |
| 既存入口の次課題 | learning/subjects/information-retrieval-search/README.md:22 | 語の頻度と文書長を変えるTF/IDF・BM25対照 |
| 既存続編 | learning/continuations/information-retrieval-search/precision-recall-contract/coverage.json、TF/IDF/BM25未対応 | 集合のprecision/recallを順位付けの証拠へ流用しない |
| 既存Skill | subjects/information-retrieval-search/skills/atlas-information-retrieval-search/SKILL.md | BM25は現在未対応と案内される。独立した有限根拠への新しい案内を作る |
| Manning/Raghavan/Schütze, Introduction to Information Retrieval | [Okapi BM25](https://nlp.stanford.edu/IR-book/html/htmledition/okapi-bm25-a-non-binary-model-1.html)、式84–86と直後のk1/b説明 | 式86のln(N/df)、tf、文書長、平均長。式85の別IDFと混ぜない |

原典ページは正式webツールで読取済みです。式86の表示画像locatorは同ページの `img771.png`。本文をローカル取得する1回の試行はDNS解決失敗で、sources/retrieval.jsonに保持しました。連続retryはせず、読取済みweb表示と独立担当の確認へ結びます。元HTMLのバイト列・SHAは未取得です。

TF×IDFは長さで正規化しない比較基準として独自に固定し、BM25は原典式86の有限条件とします。IDFの自然対数の底、空文書の数え方、非一致の候補除外、同点ID順はCONTRACT.mdへ明記しました。これらを製品共通の挙動とは呼びません。

既存catalogと旧127・独立受入の読取では、この単元と同じ順位対照の実装済み記録を確認していません。PC全体の不存在は主張しません。元ownerの現在状態は不明のため共有repoはread-onlyとし、この独立pathだけに制作します。台帳へ自己加算しません。

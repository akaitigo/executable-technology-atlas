# 実行範囲と未教材

この教材のdenominatorは5 document・3 snapshot・13固定query。分野全体のcoverage件数ではありません。

| 範囲 | この教材の確認 |
| --- | --- |
| 転置index / AND / OR | Python実postings、集合step、result rows、独立full scan |
| 更新異常 | rebuildしない状態のstale hitとmissing hitをそれぞれ1件保持 |
| 回復 | 更新後rebuildの2 queryがfull scanと一致 |
| 境界 | case/句読点/重複term/空query/未知term/未知term混合/ASCII限定 |
| 証拠 | 実時刻/runtime/input/source/Artifact digest、通常checker read-only |

未教材: relevance/ranking/BM25、phrase/NOT/複雑式、stemming・日本語形態素、semantic embedding、製品engine、incremental update・並行更新・永続化・障害回復、アクセス制御、大規模分散検索、性能/容量benchmark、評価collection/precision/recall。全Subjectは未完成で、この1教材の結果を未教材領域へ転用しません。

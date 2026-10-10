# 検索品質：適合率（precision）と再現率（recall）

前提: document ID、Boolean AND/OR、集合と分母。[既存転置index教材](../../../subjects/information-retrieval-search/README.md)の「検索品質評価」へ進む有限続編です。Python標準ライブラリだけを使い、架空の5documentと作者指定relevance集合{d1,d2}をproducer実行前に固定します。

1. AND/ORがscanとindexで一致すれば品質も両方1になるか予想する。
2. `python3 verify.py`で記録と独立期待値を照合し、`python3 serve.py`のURLで[UI](index.html)を開く。
3. 条件・label契約を選び、予想→実装一致と品質指標→ID別分類を比較する。空返却と全返却も操作する。
4. 原典・実装・rawへ戻り、答えと実務判断を説明する。予想変更では新しい値を保ち旧比較/答えをclear、条件変更では予想もreset、不正row入力では既存の予想対照を維持する。

主要概念: queryはblue green。d1=Blue green guide、d2=Blue field manual、d3=Green inventory log、d4=Blue glossary、d5=Gold audit memo。合成の「案内文書探索」という情報要求に対し、作者がd1,d2を関連と指定した外部labelです。検索結果から逆算したlabel、実利用者の判断、製品品質の証拠ではありません。

| 条件 / 返却 | precision | recall | ID別の意味 |
|---|---|---|---|
| AND / d1 | 1 | 1/2 | d1 TP、d2 FN |
| OR / d1,d2,d3,d4 | 1/2 | 1 | d1,d2 TP、d3,d4 FP |
| 空query・未知語 / 空 | undefined (0/0) | 0 (0/2) | d1,d2 FN |
| 全返却診断 / 全5件 | 2/5 | 1 | d3,d4,d5 FP |

scan/indexは全ケース一致するが、それだけでprecisionとrecallが両方1とは言えない。ALL_DIAGNOSTICはqueryを無視する明示診断で、Boolean検索やrankingの優れた方式と呼ばない。空queryは返却0の独自契約。tokenはASCII小文字英数字、重複を除く。[Stanford原典 / equations36–39とcontingency table](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-unranked-retrieval-sets-1.html)で、precision=TP/(TP+FP)、recall=TP/(TP+FN)を確認する。

label契約: 指定{d1,d2}は通常判定。明示的な空関連集合[]は全件を既知非関連と判定し、recall分母0をundefinedにする。返却も空ならprecisionもundefined。labels=Noneは未評価で、TP/FP/FN/TNと両指標はunjudged。未判定を非関連や0点へ変換しない。分母0を勝手に0または1に埋めない。

独立期待値: [固定corpus/query/label](fixture.json)、[ID別の手書きTP/FP/FN表](hand-oracle.json)。[独立oracle](source.html?file=oracle.py)はproducerをimportせず、固定token表と文字単位tokenizerで返却を求め、四つの分類cellをIDごとに足しFractionで計算する。producerの集合共通部分/差分だけをコピーしない。[scan/index/quality実装](source.html?file=retrieval.py)、[checker](source.html?file=verify.py)、[実測raw](observations/attempt-01/raw.json)へ辿る。

実務判断: corpus/query/token契約とrelevance判断を別に固定する。実装一致は内容の取り出し方、品質評価は指定labelに対する返却集合の性質。precisionとrecallを一つの「品質100%」へ丸めず、分母・FP/FN・未判定を追跡する。

[RAGの根拠と回答](../../../subjects/generative-ai-rag/README.md)では、検索文書からcontext・引用・回答の支持へ進みます。今回の適合率・再現率が高くても、回答の主張が根拠で支持されるとは限りません。

入力契約: corpus1..32、unique d数字ID、ASCII text0..256/query0..128、AND/OR/ALL_DIAGNOSTIC。returned/relevantは重複なしのcorpus内ID（labelなしNoneは受理）。不正入力と正常な空返却・undefined/unjudgedを分離する。UI rowは整数0..4。

限界: ranking、ユーザー評価、製品検索、性能、意味理解は未測定。原典は[source locator](sources.json)、未教材と次3実験は[coverage](coverage.json)、[検証記録](VERIFICATION.md)、[有限Skill](skills/atlas-precision-recall-contract/SKILL.md)。全Subject/Atlas完成ではない。

明示記録は`python3 verify.py --record attempt-01`（未使用名限定）。通常checker/route/UIは固定attempt-01を読む。`--seal-record`はrawを保持しQA/source receiptを更新する。旧教材は変更しない。

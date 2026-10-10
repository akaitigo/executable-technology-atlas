# Data governance / quality / lineage — 使ってよい結果かを確かめる

固定された架空のproducts/categoriesに品質contractとlineage DAGを適用する有限教材。Python標準ライブラリだけで16ケースを実行し、手計算した違反のtable/row/column/rule、集計行、graph異常、cache失効を独立oracleで照合する。実データ・PII・会社policyの認定を含まず、科目全体の完成ではない。

前提は表の行/列、キー、nonnull、DAGの辺、内容hash。学習の道筋は「品質条件を明示 → batch受理/拒否 → 結果の由来を列まで辿る → source変更で古い結果を失効 → 実務の例外・所有者・標準形式へ」。[index.html](index.html) でdecision・違反数・graph有効性を予測し、ケース/集計列を選択して比較する。画面は保存済みの実行readerであり、その操作はengineの再実行を行わない。原入力・contract・raw command/trace・手計算答えを辿れる。

前単位 `data-engineering-orchestration` はCSV ingest・typed変換・dedup/quarantine・generation公開とrerunを実装した。本教材はすでに型を持つJSONのneutral datasetへ受理条件を適用し、batch全体を拒否する。さらに列lineageとsource/contract/lineage/producerの内容bindingからcacheの有効性を判断する。CSV parseやpublish/retryの実装を重複して広げない。

contractはproductsのid/category/amount/classをnonnull・非空、amountをboolを除いたintegerかつ0..1000000、idをunique、categoryをcategories.idへのreferenceとする。string列の空白だけの値はtype違反。categories.idもnonempty string/uniqueを検査する。classは説明用のpublic/internalだけを受け入れ、集計は対象行にinternalが含まれるとinternalにする。これはアクセス制御、PII検出、匿名化、実際の会社分類policyを強制しない。

通常のp1=(c1,100,public), p2=(c2,0,internal)はc1合計100、c2合計0となる。0・1000000・空batchも受理。nonnull、range上下超過、duplicate id、missing reference、未知classは全batch拒否。combined-badはp1のamount=-1/category=c9/class=secretを3違反として列まで記録する。重複idのfixtureは1行目p2、2行目p2なので違反は2行目に位置する。

lineage DAGは products/categories → validated → totals。集計amount_sumはvalidated.amountからproducts.amountへ辿り、categoryはproducts.categoryとcategories.idを辿る。入力graphの未知parentはTopologicalSorterが自動でnodeとして扱い得るため、独自のorphan検査で先に拒否する。cycle、未知列、targetのancestorでない列edgeも拒否する。今回の16ケースで実行したgraph異常はcycle/node orphan/column orphan。nonancestorの分岐は実装済みだがfixture未実行で次の実験に残す。

同じsourceの固定cacheはreused。p1.amountを100→101へ変更するとproducts source hashが変わりinvalidatedとなり、古いc1=100は再利用せず結果は空にする。cache失効後の再計算は別実験であり、このfixtureは古いcacheを止めるところまで。source・contract・lineage・producerにbindingするので変われば失効する。contract/lineage/producer変更のfixtureは未実行。cacheは教材で与えた信頼済みの固定値。悪意ある出力とdigest両方の改変をhashだけで検出できず、独立oracleが今回の意味を保証する。

実務で判断できるのは、成功exitに加え受理条件の違反を確認すること、nonnullとrange/unique/referenceを区別すること、graphが有効でもsource変更で結果が古くなること、hashと業務承認を混同しないこと。不正行を隔離して進める前単位の方針とbatch全体拒否は、要求によって選ぶ。定義されたcontractに通ることはデータが現実に正しいことやpolicy準拠の証明ではない。

```sh
python3 runner.py                      # 既存証拠のread-only確認
python3 checker.py
python3 test_negative.py               # disposable copy 5種の改竄 + read-only確認
python3 runner.py --record             # 明示した原票更新時だけ
python3 preview.py                     # 動的loopback、一時preview終了時Ctrl-C
python3 skills/atlas-data-governance-quality-lineage/route.py contracts-lineage
```

[current.json](current.json) からUTC時刻/OS/Python、case input、stdin/stdout/stderr/exit、trace、result、手計算oracle、source/artifact SHA256へ到達する。[checker.py](checker.py) はengine/runnerをimportしない。固定入力、違反位置、DAG order、列対応、合計値まで比較しdefaultはread-only。[qa.json](qa.json)・[verification.json](verification.json)・[ui-observations.json](ui-observations.json) に実IABと検証を保存する。

主要な未カバー領域はownership/stewardship、contract evolution、分布drift/threshold、PII/consent/retention/access、cross-system standard lineage、変換式の意味的監査、cacheの真正性。[coverage.json](coverage.json) に具体的な問いと次の4実験を資料へ対応させている。大規模distributed catalog、外部scheduler、PROV/CSVW準拠、security certificationは実行していない。

一次資料: [W3C Tabular Data Model](https://www.w3.org/TR/tabular-data-model/) §4.6/§6.6 の型・制約・validation、[PROV primer](https://www.w3.org/TR/prov-primer/) §2 のentity/activity/derivation、[Python graphlib](https://docs.python.org/3/library/graphlib.html) のpredecessor mapping/TopologicalSorter/CycleError、[hashlib](https://docs.python.org/3/library/hashlib.html) のSHA256。[sources.json](sources.json) にlocatorと確認日を保存する。この教材のJSON形式がこれら標準へ準拠するという認定ではない。

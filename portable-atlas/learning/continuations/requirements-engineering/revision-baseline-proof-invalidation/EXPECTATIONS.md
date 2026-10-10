# 実装前の有限契約と手表

6固定ID R-CAP/D-CAP/T-CAP と R-FIFO/D-FIFO/T-FIFO、各nodeはrev1..9と64桁lowercase SHA-256 metadata。各linkはsource/target/rev、R→DまたはD→Tのみ、cross枝を許す。重複edge不可、最大8本。内容そのもの/実製品sourceを入力しない。hashは合成metadataであり署名ではない。

old/new graphとproofsのexact3field。graphはnodes/links、nodeはid/rev/hash、linkはsource/target/rev。6IDを各1、順序は意味なし。revisionはbool不可。proofはtest/result/baseline、result PASS/FAIL、test既知・重複不可。baselineはnodes/links、subsetの既知IDと型を検査する。proof最大2。

1. graph baselineは全nodeのID、R/Dのrevision/hash、全linkのendpoint/revision。Tのrevision/hashは除外。oldとnew digestが違えば旧到達cacheは適用不可・再計算必要。new到達を計算すること自体は実test再実行ではない。
2. 各test baselineは逆方向に辿った全ancestor＋testのrevision/hashと、その祖先部分graphのlink/revision。stored proofと現在baselineをexact比較する。PASS文字列だけで現在証拠にしない。CAP枝変更でも未影響FIFO枝のproofは適用可。test実装変更だけならgraphは再計算不要、当該proofはSTALE。
3. canonical4関係はこの教材で要求したlink一覧として明示。新graphで各testに必要な関係を1本でも欠くならUNKNOWN_TRACEを優先し、old proofが一致しても現在PASSにしない。現在到達は保存link内の部分結果、影響なし・link完備とは呼ばない。canonical完備は有限契約だけで製品の全関係完備ではない。
4. 判定優先はschema拒否→実Error→各test UNKNOWN_TRACE→MISSING→baseline不一致STALE→CURRENT_PASS/CURRENT_FAIL。人の承認は常にUNCONFIRMED、実test再実行は常にfalse。
5. graph変更の起点は変わったR/Dと、追加/削除/revision変更したedgeのsource。old/new両graphで下流到達の和をimpactとする（削除後の枝も忘れない）。testだけの変更はこのgraph impactから除外しproof判定に出す。impactは再testを選ぶ材料で実test結果ではない。

|条件|再計算|CAP旧証拠|FIFO旧証拠|到達/影響の要点|
|unchanged/same-hash/reordered|不要|CURRENT_PASS|CURRENT_PASS|同baseline|
|requirement-revision/content/same-hash-new-revision|必要|STALE|CURRENT_PASS|CAP3ID、同hashでもrevisionで失効|
|test-revision/content|不要|STALE|CURRENT_PASS|graph unchanged|
|link-revision/design-revision|必要|STALE|CURRENT_PASS|D-CAP,T-CAP影響|
|missing-link|必要|UNKNOWN_TRACE|CURRENT_PASS|新CAP R,Dのみ、旧Tも影響に残る|
|cross-link-add|必要|CURRENT_PASS|STALE|CAPからT-FIFOにも到達|
|fifo-revision|必要|CURRENT_PASS|STALE|FIFO3ID|
|old-proof|不要|STALE|CURRENT_PASS|graphとproofを分離|
|missing-proof/current-fail|不要|MISSING/CURRENT_FAIL|CURRENT_PASS|PASSは補完しない|
|empty-links|必要|UNKNOWN_TRACE|UNKNOWN_TRACE|要求自身だけ、旧両枝6ID影響|

[固定literal](oracle.json)22条件と[編集literal](custom-oracle.json)4条件をproducerより先に保存。producerはDFS、別oracleはBoolean行列の推移閉包・canonical serializationで全出力を検算。拒否4件と実RuntimeError1件も原票に残す。通常runner/checkerはread-only、明示recordのみUTC/UUID新原票、成功だけcurrentへ昇格する。

UI全3入力変更は旧graph/proof表/図/raw/答えを消し閉じ、新入力と他欄は保持。条件変更は全入力初期化。受信済み旧結果の保留・変更後のreleaseはversionで破棄。拒否/実Error/注入HTTP503では正常答えを隠す。503は自然通信障害の実証ではない。

Cross枝の保守的境界: T-FIFOにD-CAP→T-FIFOを追加すると、FIFO固有枝と現在ancestor所属CAP枝のcanonical全関係を必要とする。CAP側D-CAP→T-CAPが欠ければT-FIFO自身への経路が残っていてもUNKNOWN_TRACE。これは独自の保守的契約で、一般的な精密変更影響ではない。

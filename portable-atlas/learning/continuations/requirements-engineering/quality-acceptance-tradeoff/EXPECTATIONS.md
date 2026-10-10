# 実装前の有限契約と手表

架空needs N-FAST:短い待ち、N-RIGHT:正しい内容。架空用途U-RECEIPTは単一候補へ3件の既知応答S1/S2/S3を依頼し、全内容と受信完了時刻を比較する。期待値はS1=2,S2=4,S3=6。負荷/ネットワーク/PC測定をしない。elapsed_msもoutputも合成fixture宣言。今回Pythonが実行するのは宣言データの評価である。

R-CORRECT: 3件全output観測時、正答数/3 >= min_accuracy_bp/10000。cross multiplicationで判定し丸めで合否を変えない。R-TIMELY: 3件全elapsed観測時、各elapsed_ms <= deadline_ms（最大値で同値）。閾値はold/newの独自受入契約。R-CORRECT AND R-TIMELYでPASS、どちらか既知FAILならFAIL、残りUNKNOWNならINSUFFICIENT。速さが正答不足を相殺するweighted score/ORを用いない。実利用者の閾値決定や承認ではない。

各criterionは欠けたsample/nullがあればUNKNOWNを優先し、品質/時間を独立に判定する。観測不足を0ms/正答扱いにしない。known FAIL＋UNKNOWNは総合FAIL。正答数は観測済みの数を表示するが母数は固定3、未知を不正解と断定せず合否はUNKNOWN。accuracy_bpは全3output時だけ切捨て表示、整数count基準の合否と分離する。

Paretoは全3output/time観測済み候補だけ。正答数が同等以上かつworst_msが同等以下、少なくとも一方strictでdominate。tiesは互いをdominateせず両方frontに残す。frontはthresholdと独立、非受入候補もfrontになり得る。不足候補はeligible=false、座標はnull、図では未観測一覧へ出す。旧新閾値比較は同じデータを再評価し、観測データを取り直したとは呼ばない。

入力exact purpose/old/new/candidates。purpose固定synthetic-three-receipts。threshold exact min_accuracy_bp整数0..10000/deadline_ms整数1..1000。bool拒否。candidate0..6、ID A..F一意、samples0..3（S1/S2/S3一意）、sample exact sample/output/elapsed_ms、output null又は整数0..9、elapsed null又は整数0..1000。extras/unknown/refusalは正常答えなし。list順は無意味、ID/sampleでソート。実RuntimeError注入は別失敗。空候補はOBSERVEDだが合格候補なし、十分データ/目的達成とはしない。

|候補|正答/3|worst ms|old 100%/100ms|new 33.33%/100ms|new 100%/150ms|Pareto|
|A 速い誤答|1|30|FAIL|PASS|FAIL|front|
|B 正しい遅延|3|140|FAIL|FAIL|PASS|Cにdominated|
|C 両方|3|80|PASS|PASS|PASS|front|
|D 劣る|1|120|FAIL|FAIL|FAIL|A,Cにdominated|
|E S3不足|観測2|未観測|INSUFFICIENT|INSUFFICIENT|INSUFFICIENT|除外|
|F 全null|観測0|未観測|INSUFFICIENT|INSUFFICIENT|INSUFFICIENT|除外|

固定20条件・編集4条件のliteralはproducer前に保存。deadline等値はPASS、1ms超過FAIL、C/D同座標は両方front、C worst200ならfront A/Bでも合格0、C時間/出力欠落はUNKNOWN、既知時間FAIL＋品質UNKNOWNはFAIL。output/threshold/order/schemaの変異を別oracleで検査する。

常にapproval=UNCONFIRMED、validation=UNCONFIRMED、measurementSource=synthetic-fixture、testsExecuted=false。digestは改変検出、署名/品質要求の正しさではない。通常runner/checker/serverはread-only/memory-only、明示recordだけ新UTC/UUID原票を保存し失敗はcurrentへ昇格しない。

UI全3入力変更で旧表/図/raw/答えを消し閉じ新入力と他欄は保持。条件変更/resetは全入力初期化。旧version保留結果は受取時に破棄。拒否/実Error/注入HTTP503では正常答えを出さない。503は自然障害の実証ではない。

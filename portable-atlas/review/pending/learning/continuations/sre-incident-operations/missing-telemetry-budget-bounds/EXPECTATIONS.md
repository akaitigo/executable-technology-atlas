# producer前の有限台帳と手Fraction

独立した合成発行台帳はtick0の全IDを既知とする。台帳のeligible boolで母集団を定義、collector observationsだけを分母にしない。eligible N、cutoffまでgood G/bad B、未観測U=N-G-B。arrived_tick<=cutoffは同時刻を含む。将来到着のresultを計算へ先取りしない。観測なし/lateはUNKNOWNで永久欠落やrequest品質失敗と断定しない。excluded IDは全予算計算から除外し行にはEXCLUDEDを残す。

seen-only SLI=G/(G+B)、seen0ならnull。全台帳SLI範囲=[G/N,(G+U)/N]。target=num/den、許容bad予算Q=N(1-target)はFractionで切上げ/丸めなし。bad範囲=[B,B+U]、残予算=[Q-B-U,Q-B]（negativeをclampしない）、burn=[B/Q,(B+U)/Q]。未知をgood/badへ実際に補完した結果ではなく、可能な極端の範囲。

N>0の判定: lowerSLI>=targetならCERTAIN_MET、upperSLI<targetならCERTAIN_MISSED、他はINDETERMINATE。target等値は達成。N=0はNO_ELIGIBLEでSLI/seen/burn null、Q/remainingは0という計数だけ、達成と呼ばない。target100%/Q0ではN>0でもburn null・ZERO_BUDGET、infinity/0を発明しない。target0は教育境界で推奨目標ではない。seen-onlyVerdictは条件付きの比較で全台帳判定へ流用しない。

|条件 N4|G/B/U|seen-only|全SLI|Q|残予算min..max|burn min..max|判定|
|cutoff5、D bad到着7|3/0/1|1|3/4..1|4/5|-1/5..4/5|0..5/4|INDETERMINATE|
|cutoff7、D bad|3/1/0|3/4|3/4|4/5|-1/5|5/4|CERTAIN_MISSED|
|cutoff7、D good|4/0/0|1|1|4/5|4/5|0|CERTAIN_MET|
|target3/4、未知D|3/0/1|1|3/4..1|1|0..1|0..1|CERTAIN_MET|
|A/B bad、未知D|1/2/1|1/3|1/4..1/2|4/5|-11/5..-6/5|5/2..15/4|CERTAIN_MISSED|
|全未観測|0/0/4|null|0..1|4/5|-16/5..4/5|0..5|INDETERMINATE|

入力exact target/cutoff/ledger/observations。target exact num/den、den1..10、num0..den integer/bool拒否。cutoff0..10 int/bool拒否。ledger0..6 ID A..F一意、exact id/eligible strictbool。observations0..6、exact id/result/arrived_tick、ID台帳内unique、result good/bad、arrived0..10 strictint。順序は意味なし。拒否は正常計算なし。空台帳＋空obsは有効入力NO_ELIGIBLE。空obs＋非空eligibleは全unknown。全excludedはNO_ELIGIBLE。

固定20＋編集4条件の[手答え](oracle.json)と[編集手答え](custom-oracle.json)をproducer前に保存。producer Fraction、別oracleは全未知割当0/1の列挙と整数比演算で極値/判定を検算する。cutoff同時/1後、late確定、target100/0、分母0、非整数Q、拒否4、実Errorも比較。

模型台帳が完全という明示仮定は実pipeline保証ではない。実pager/目標推奨/本番判断/人の承認はしない。approval/productionGuaranteeはUNCONFIRMED。通常CLI/serverはread-only/memory-only、recordのみ新UTC/UUID原票。UI全3入力変更で結果/図/raw/答えを消し閉じ他欄保持、条件resetで全初期化、stale拒否/正常答え非表示を検証する。

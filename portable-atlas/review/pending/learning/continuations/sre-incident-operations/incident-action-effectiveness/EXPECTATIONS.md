# producer前の有限incident/action契約

架空INC-DOUBLE: value2/期限3に対してoutput3を返す誤答。要求R-CORRECT=値を2倍、R-DEADLINE=logical tick2で完成し期限>=2ならSUCCESS、期限0/1なら予算内TIMEOUTでoutputなし。logical tickは模型のcostで実経過時間/性能SLOではない。action ACT-DOUBLEは計算と期限等値条件を修復し、7再現/regressionを再試験する。実本番incident/原因分析ではない。

[tests.json](tests.json)の手oracleを実装前固定。REPRO(2,3)→SUCCESS4/2、EQUAL(2,2)→SUCCESS4/2、SHORT(2,1)→TIMEOUTnull/1、ZERO(2,0)→TIMEOUTnull/0、VALUE0(0,3)→SUCCESS0/2、VALUE3(3,3)→SUCCESS6/2、COINCIDENCE(1,3)→SUCCESS2/2。outputとstatusとlogical costをexact比較、bool/intの混同をしない。bad=値+1/cost1/期限無視で全7失敗（COINCIDENCEでもcost違い）。partial=2倍/cost2だがdeadline>2という境界誤りでEQUALだけ失敗。fixed-v1/v2=deadline>=2、別version/source bytesだが同機能。

各試験は指定build.pyを実Python子processで起動し、stdin/UTC/argv/exit/stdout/stderr/sourceSHAを記録する。期待値はbuildを実行せず事前手表＋別oracleで照合。action doneと、source/versionに束縛された新試験は別情報。evidence_buildが指定されればその別buildも実suiteを実行し旧PASSを観測する。宣言PASSを捏造しない。

入力exact current_build/action_done/evidence_build/retest/suite。build bad/partial/fixed-v1/fixed-v2、evidence null又は同enum、flags strictbool、suite既知7IDのunique list0..7。順序は意味なし、出力はtests宣言順に実行。拒否は試験なし、実Error注入も正常答えなし。

採用proof優先: retest=trueの現在build実試験→retest=falseならevidence_build実試験→なし。判定順: action_done=falseならACTION_OPEN（behaviorVerifiedは別計算）、proofなしUNVERIFIED、current build/version/digest不一致STALE_PROOF、実試験にFAILがあればINEFFECTIVE、必要suite不足ならSUITE_INCOMPLETE、完全7PASSだけVERIFIED_FINITE。verified条件のcompleteとpassとbuild/digest一致を別出力する。action doneだけではverifiedにならない。完全suite以外から未試験境界PASSを補わない。same-build proofは今回実観測であり別の長期保管・署名機構ではない。

|条件|現在実失敗|旧build実失敗|decision|
|bad-retest|全7|なし|INEFFECTIVE|
|partial-retest|EQUAL|なし|INEFFECTIVE|
|fixed-v1/v2-retest|なし|なし|VERIFIED_FINITE|
|marked-only|未実行|未実行|UNVERIFIED|
|stale-build-pass|未実行|fixed-v1全PASS|STALE_PROOF|
|same-build-proof|未実行|fixed-v1全PASS|VERIFIED_FINITE|
|partial-with-old-pass|EQUAL|fixed-v1全PASS|INEFFECTIVE|
|open-action-pass|なし|なし|ACTION_OPEN / behavior verified|
|repro-only-partial|REPRO PASS/EQUAL未実行|なし|SUITE_INCOMPLETE|
|empty-suite|未試験|なし|SUITE_INCOMPLETE|

固定17条件＋編集3条件。有限repair有効性は合成Pythonモデルの7条件だけ。approvalとproductionEffectivenessは常にUNCONFIRMED、CAPA監査/実incident復旧/一般因果を主張しない。通常CLI/serverはread-only/memory-only、明示recordだけUTC/UUID新原票、失敗はcurrentへ昇格しない。UI全入力reset/stale/refusal境界を検査する。

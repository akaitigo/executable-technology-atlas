# Atlas：上位値で隠れる不正設定の契約

目標32の「検証時点・既定値・切戻しの方針を決める」を、同じ合成layerへの2方針で比べます。元subjectの全layer型規約とatomic-reloadの更新整合性は前提で、再実験/再加算しません。os.environの読書き・applicationへの設定適用・外部provider呼出しはありません。

## 固定入力と2方針

4fieldの走査順は timeout_ms、retries、flag_enabled、rollout_percent。default=(1000,2,true,50)、優先順は default < env-input < task-json。inputs/cases.jsonに6条件を固定します。各条件は all-layer と winning-only をこの順で、別copyから評価します。2方針は要件による選択であり、一方をPython/OpenFeatureの正規実装とは呼びません。

1. normal-boundary：env TIMEOUT='2000', FLAG='true'、task=(5000,0,false,100)。正常上書きと既存の上下限を同時に確認。
2. shadowed-integer：env TIMEOUT='oops'、task timeout=3000。
3. unshadowed-integer：同じenv不正、task retries=3。timeoutは隠れない。
4. invalid-winning-bool：env TIMEOUT='2000'、task timeout=true。boolをintへ通さない。
5. shadowed-boolean：env FLAG='TRUE'、task flag=false。大文字不正をnative falseで隠す。
6. unknown-field：env APP_SECRET='EXAMPLE_NOT_A_SECRET'、task timeout=3000。上書き方針より前の共通構造拒否。

## 両方に共通する構造段階

rootのlayer集合はdefault/env-input/task-jsonのみ、各layerはobject、defaultは既知4fieldを全て持つ。envはAPP_TIMEOUT_MS/APP_RETRIES/APP_FLAG_ENABLED/APP_ROLLOUT_PERCENTを対応付ける。taskは既知4fieldのみで、env/taskは部分指定可。layer順に、未知fieldはnameのsort順で最初を拒否する。構造不正が1つでもあれば型parseやmergeを始めない。unknown-field診断はlayer/source_field/reasonだけで、そのraw値を結果・eventへ転載しない。今回の実対照は未知field1件のみで任意schema拒否の全検証ではない。

## 型規約と検証順

元evaluator.pyの規約を再利用する。env値は正確なstr。booleanは小文字'true'/'false'のみ。integer文字列はregex `-?(?:0|[1-9][0-9]*)` のfullmatch後にint化する（空白、先頭+、先頭0の追加を受理しない）。native booleanはtypeがbool、integerはtypeがintでboolを除く。timeout 1..5000、retries 0..5、rollout 0..100。型→範囲の順。

all-layerはlayer順、各layer内の上記field順で全present値をparse/範囲検査する。最初の不正で停止し、後続layerへ進まない。全合格後にtyped値を優先順で合成する。これは旧evaluatorの全error蓄積とは違う、最初の拒否を読みやすくする本教材の規約である。

winning-onlyは構造合格後、型parse前にraw値とlayer/source_fieldを優先順で合成する。4つの勝者だけをfield順でparse/範囲検査し、最初の不正で停止する。隠れたrawを型検証済みと呼ばない。raw合成は採用/成功ではない。

## 公開結果と診断

成功時だけconfigとprovenanceを公開する。provenance[field]はlayer/source_field/raw/typed。拒否時は両方null。diagnosticには検査済み/拒否したparse_attemptsと候補candidate、errorを保存するが、利用可能configではない。candidateはall-layerでは全検査合格後のtyped合成だけ、winning-onlyでは構造合格後のraw合成だけ。拒否したfieldのtypedはnull。

各eventはdeep copyで index/action/layer/source_field/field/reason と、その時点の parse_attempts/candidate/config/provenance/error を保存する。START→STRUCTURE_OK、all-layerはPARSE_OK列→MERGE_TYPED→COMMIT、winning-onlyはMERGE_RAW→PARSE_OK列→COMMIT。型拒否はPARSE_REJECT→REFUSE、構造拒否はSTRUCTURE_REJECT→REFUSE。拒否後にeventは増やさない。event内config/provenanceはCOMMITだけ非null。

通常の判定拒否はtargetの正常終了と分ける。12結果の合成模型が全て完了すればCLI exit0/complete true。実行例外/期限超過/入力が読めない場合は実行失敗として保存し、成功を作らない。

## 有限受入と実行

手期待は実装前に固定し、独立担当が別に期待を保存してからproducerを制作する。全12結果のdecision/診断/parse順/候補/公開値/由来と全eventを照合する。正常/隠れる不正/隠れない不正/勝者bool/未知fieldが主眼で、任意入力、秘密保護全般、JSON重複key/巨大数、migration、reload、rollout、provider適合、可用性は対象外。

rootだけがfresh資源/単独枠で標準Python1子、nice10、外側wall5秒、再試行0を管理する。作者は模型/GUI/serverを起動しない。実行前は未実測と表示する。GUIはrootの既存pageで保存値を読み、条件/方針/予想/resetが旧表示を消すことを確認する。共有元/完成186/台帳はread-only、未統合/作者加算0。

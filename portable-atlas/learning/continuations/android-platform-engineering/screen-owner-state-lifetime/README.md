# screen ownerと状態寿命 — 回転と再作成は同じか

Python標準libraryだけの明示2screen owner模型。A state2/B state1から回転・finish・deathを比較する。実Android SDK/Compose/ViewModel/SavedStateHandle/OS process再開は実行しない。

## 前提と読む順番

object寿命、state machine、JSONが前提。

1. [Activity/process入口](../../../subjects/android-platform-engineering/README.md)でinstance破棄とprocess deathを分ける。[元coverage次1](../../../subjects/android-platform-engineering/COVERAGE.md)が今回の根拠。
2. 本単元の[事前契約](EXPECTATIONS.md)と[26行の固定owner/view/state表](oracle.json)を読み、2予想を立てる。
3. [UI](index.html)でB回転→finish→再B→death、正常/故障を実Python比較。
4. [一次資料との対応](SOURCES.md)・[実装](producer.py)・[独立照合](oracle.py)へ戻り、条件に合う答えを開く。
5. [version付きCodable presence](../../apple-platforms-engineering/versioned-codable-presence/README.md)等の保存codecで存在/null/version/typeを考える。保存とin-memory寿命は別の契約。

## 固定契約と実務判断

初期process1 alive、A=p1:A:1/view1/state2、B=p1:B:2/view1/state1。screen名Bとowner identityは別。rotateは同owner/state、view generationだけ増加。finishはowner/stateを除去。createは新serial/状態0。deathは全in-memoryを消去しdead。restartはPythonの明示操作でprocess番号を増やした空模型を作る。

|条件|A最終|B最終|process/alive|
|---|---|---|---|
|B回転|p1:A:1/view1/state2|p1:B:2/view2/state1|1/true|
|B finish|同じA|なし|1/true|
|finish→新B|同じA|p1:B:3/view1/state0|1/true|
|death|なし|なし|1/false|
|death→restart模型→B|なし|p2:B:1/view1/state0|2/true|
|global漏れ故障/B回転|p1:A:1/view1/state1|p1:B:2/view2/state1|1/true|
|dead owner再利用故障|同じA|p1:B:2/view2/state1|1/true|

A回転、B2回転、B増分、初期だけも含む11正常/故障case、9入力/transition拒否、実RuntimeErrorの21case。故障の観測表も先固定し、正常契約に照らして違反を説明する。故障modeにevent JSONを上書きして変化がない場合にも、故障が必ず発現したと答えない。

event0..8、厳密op/target、A/Bのみ。create/rotate/finish/tap、target nullのdeath/restart。未知mode/op/target、既存create、ownerなし操作、dead screen操作、生存restart、不正構造/JSONは拒否。tapは0..9。拒否/実Errorのtimeline/finalはnull、正常答えなし。正常のowner空表とは区別する。

## 実行と証拠

このディレクトリで。追加install・Docker不要。

```sh
python3 -B runner.py --case rotate-b
python3 -B runner.py --case recreate-b
python3 -B runner.py --case process-death
python3 -B runner.py --case global-leak
python3 -B runner.py --case dead-owner-reuse
python3 -B runner.py --case rotate-finished  # 意図的拒否 exit2
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py lifetime
python3 -B runner.py --record  # 明示保存だけ
python3 -B server.py
```

通常runner/checker/routeはread-only。明示recordはUTC/UUID名の新rawを追加、旧原票を保持。実子processのcommand/UTC/exit/stdout/stderrとsource SHAを記録。[current](evidence/current.json)・[binding](evidence/binding.json)・[QA](evidence/ui-qa.json)・[検証](evidence/verification.json)へ結合。想定外失敗をcurrentへ昇格しない。HTTPは同producerを実呼出するが子processではない。

serverが印字する動的127.0.0.1 URLで操作、終了は自分のserverへCtrl-C。配信は本単元と明示3参照文書のread-onlyのみ。元Subject/共有Portal/旧教材を変更しない。

## UIから学ぶ

予想→実計算→正常/故障→実装・原典→答え。条件選択だけでは計算しない。全3入力（owner予想・state予想・event JSON）は成功比較→開いた答え→その入力だけ変更で、新値と他欄を保持し旧比較/raw/table/final/答え本文を消し閉じる。条件resetは両予想/JSONも消す。拒否と実Errorは予想・status/理由を表示し、正常答えを出さない。

受信済HTTP payloadの描画だけを保留し、条件/入力変更後の古いversionを破棄する対照。sleepなし、通信遅延測定ではない。IAB画像は実capture bytesを保存し、説明表をcaptureと呼ばない。

## 今回できる判断と未教材coverage

値をどのownerへ置くか、再生成viewと終了ownerをどう分けるかを判断できる。rotation保持をprocess death後の永続性に読み替えず、finish済ownerの再利用とglobal漏れを別に検査する。

次の未実施実験は①saved tokenのfreshness/type/versionと復元、②navigation graph owner/keyの多重scope、③対応SDK/deviceで回転/finish/deathの実測。実Android/Compose/SavedStateHandle/Bundle、back stack全規則、async cancellation、実OS kill/restart、保存・性能・security/API/OEM保証は未実証。

[有限Skill](skills/atlas-screen-owner-lifetime/SKILL.md)は既存runner/UI/checkerへ限定route。global installや独立agent evalではない。Core/fullGate/commit/push/公開はこの有限課題では未実行。Subject/Atlas全体の完成ではない。

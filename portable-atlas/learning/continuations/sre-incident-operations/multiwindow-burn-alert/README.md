# Multiwindow burn alert — short / long と AND

[元SRE教材の次実験](../../../subjects/sre-incident-operations/README.md)を進める独立continuation。分母とerror budgetから、重なる2窓でのburn判定へ進む。元Subjectと他教材は凍結したまま。

## 前提 → 予測 → 操作 → 比較

前提は整数の失敗数／対象数、半開区間、分数、bool。主要fixtureはID0..99の100event、tick=id、good/badの2分類で全件eligible。long [0,100)、short [90,100)、toy SLO=9/10、許容失敗率=1/10。burn=(失敗/対象)/(1/10)。独自policyは**両burn >= 2のAND**。本番pager/SLO設定の推奨ではない。

python3 preview.py の専用動的loopback URLを開く。case・AND／短窓だけの誤比較を選び、short burn／long burn／判定を予測する。「観測と比較」で分母、失敗ID集合、Fraction、両比較、rawを照合する。caseまたは判定方法を変更すると前の予測・結果・答えをclearする。入力拒否時も予測対照とrawを読め、falseへ変換しない。

|100event条件|失敗ID|short burn|long burn|AND|短窓だけの誤比較|
|---|---|---|---|---|---|
|正常|なし|0|0|false|false|
|突出spike|96,97,98,99|4|2/5|false|true|
|持続sustained|0..17と90,91|2|2|true|true|
|長窓履歴recovered|0..19|0|2|false|false|

Sustainedの両2は>=によってtrue。spikeの短窓だけtrueをANDへ流用してはいけない。時刻・回復の語は合成窓の配置を説明するもので、実incidentの回復を観測した主張ではない。

## 入力と窓の有限契約

eventはexact keys id/tick/status。idは非負intでunique、tickはint（boolを拒否）、statusはgood/bad。event IDは識別で、窓はtickで選ぶ。fixtureではtick=idだが、識別子と実clockを同一概念にしない。窓外eventも型検証し、集計対象から除外する。

境界fixtureはbad IDs 89,90,99,100の4event。long対象89/90/99、short対象90/99、100は両窓外。対象3／2、失敗3／2で両burn10、AND=true。これは100event主要fixtureとは別の小さな境界検査であり、欠測補正を表さない。

short-emptyは0..89 goodのみ、long burn0／short分母0でexit2。all-outsideは100..199 good、emptyは0eventで両分母0。未知status、重複ID、boolean tickは入力検証で拒否し窓を計算しない。全11ケースの正常計算exit0は5、契約拒否exit2は6。拒否を成功計算やfalseへ混ぜない。

## 実装・raw・再現

- [期待値](expected.json)は実行前に手書き。[worker](worker.py)は整数count＋fractions.Fraction、[独立checker](checker.py)はproducerをimportせず別のevent ID集合とliteral分数/bool/拒否を照合。整数×分数不変式も検査する。[観測runner](runner.py)は実subprocessのcommand/input/UTC/exit/stdout/stderrを保存。
- [CURRENT](CURRENT)に現在のrun。input.json、stdout.json、stderr.txt、expected/worker copy、result.json、artifact bytes/SHA256を保存。UIは保存観測だけを読み、計算をJavaScriptへ複製しない。
- python3 runner.py / checker.py / route.py inspect はread-only。新規観測の明示指定時だけ python3 runner.py --record / route.py record。UTC別runへ追記し旧rawを保つ。
- python3 test_negative.py はraw/derived/hashを整合した7改変を一時copyで独立拒否。通常経路の全file SHA256/mtime_ns不変を確認。
- [QA](QA.json)、[coverage](COVERAGE.md)、[module Skill](skills/multiwindow-burn-alert/SKILL.md)。route lessonはUI位置、未知routeはexit2。個人絶対pathは保存しない。subprocess runtime pathだけ名前へ正規化する。

## 原典と実務判断

[Google SRE Workbook: Alerting on SLOs, §6 Multiwindow, Multi-Burn-Rate Alerts](https://sre.google/workbook/alerting-on-slos/)で長窓と短窓をANDする考えを確認した。原典のSLO、窓比、burn閾値、複数levelをこのtoy値に置き換えて本番推奨とは呼ばない。今回のSLO90%、short/long=1/10、>=2は独自の教育契約。

実務で必要なのはeligibleの定義、収集欠落、traffic量、期間、閾値、reset、利用者影響の確認。synthetic datasetのAND=trueからpagerやrelease停止を決めない。実clock、欠測／遅着補正、実monitoring/incident/on-call、stream frameworkは未実行。次の3実験と未網羅はcoverageへ。SRE/Atlas全体のcompleteではない。

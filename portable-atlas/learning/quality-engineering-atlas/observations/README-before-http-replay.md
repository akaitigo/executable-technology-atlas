# QE Atlas — 品質を要求・測定・検証・改善でつなぐ

[日本語入口](index.html)から、品質要求→測定と利用者結果→テスト設計とリスク→統計/SQC/実験計画→信頼性/SLO→改善/予防へ進む。Taguchi品質工学/ロバスト設計は独立章とする。QEをtestツールの一覧やHTTP200の率だけへ縮めない。

**使える新教材は「server HTTP200とclient 2秒timeout」1単元。** 全章の入口と[coverage](COVERAGE.md)は用意したが、QE分野全体の網羅、利用者validation、品質認証、実サービス安全性は未達。以下の既存教材は相対リンクで再利用し、本文・実装・原票をcopyしない。

- [Requirements](../subjects/requirements-engineering/README.md): 要求ID/revisionと検証matrix。誰のneedsを満たすかの承認は別。
- [SoftwareQuality](../subjects/software-quality-engineering/README.md): 行coverageと境界mutation。高coverageは品質全体の証明ではない。
- [Math](../subjects/mathematical-statistical-foundations/README.md): 条件付き確率/分母/base-rate。統計的推定を今回実行したとはしない。
- [SRE](../subjects/sre-incident-operations/README.md): SLI/SLOのgood/eligible、窓とerror budget。今回のlatency観測へつなぐ。

## 最初の教材の有限契約

実行前[hand-oracle.json](hand-oracle.json)に6request列、deadline、観測窓、分母、分位点、打切りを固定。delay単位は整数ms、request r1..r6が模型t=0に独立到着し、待ち行列・network jitterはない。

| 列 | planned server delay ms |
|---|---|
| slow | 100,200,400,800,1800,2200 |
| boundary | 100,200,400,800,1800,2000 |
| healthy | 100,200,400,800,1000,1200 |

模型deadlineは1000/2000ms、窓末尾1500/2500ms。12条件。`delay <= deadline`かつ`delay <= window`ならclient RECEIVED_200。deadlineが窓内にありdelayが超えればCLIENT_TIMEOUT。窓が先ならPENDING_AT_WINDOW。deadlineと同時のresponseを受理するのは模型のイベント規則で、実socket境界の保証ではない。server200生成/試行はdelayが窓内のときだけ観測された扱い。生成/試行とclient受信は別列。

利用者結果の分母は全6発行request。窓内確定deadline達成率=受信成功数/6。pendingがあると最終結果は未確定なので、確認済み率と `(成功+pending)/6` 上限を表示する。pendingを失敗・成功へ勝手に置換しない。client response-status率の分母はclientが実際に受信したresponseだけ。server200試行率の分母は観測されたserver試行だけ。どちらも100%でも、全要求に対するdeadline達成率とは一致しない。

received-only平均/p50/p95は受信したresponseへの条件付き。nearest-rankは昇順の `x[ceil(p*n)-1]`、補間なし、空なら未定義。p50は偶数件の補間中央値ではない。NISTは複数方式と差を説明しており、このnearest-rankをNISTのdefault法とは扱わない。20件中19件100ms・1件2200msならp95=100ms、最大2200ms。p95でも隠れるtailがあり、少数実HTTPから母集団p95を一般化しない。

全要求の `observed_wait_ms=min(delay,deadline,window)` は観測待ち時間という別metric。timeout/pendingの真のresponse latencyは不明（null）、打切りIDを表示し、deadline値を真のlatencyとして代入しない。全response latencyの平均/分位点は未推定。モデルには全planned delayが既知だが、観測で未知の値をmetricへ持ち込まない。

slow/2000/2500ではclient成功5/6、client受信response200は5/5、server200試行6/6。受信平均660ms・p50=400ms・p95=1800ms。全要求の観測待ち平均2650/3ms・p95=2000ms。r6の真のresponse latencyはclient観測では不明。窓を1500msへ短くすれば4成功・2pending、確定4/6と上限6/6となる。

## 別processの実HTTP

[actual_http.py](actual_http.py)は自分の動的loopback serverと独立client processを起動し、100ms応答/2200ms遅延を各1件、socket timeout2.0秒で観測し、所有serverだけ終了する。模型の12条件は実HTTP負荷試験ではない。client processは別PID、server rawとclient rawを同じrequest ID・UTCで対応付ける。経過時間は各process内のmonotonic差分を使い、Mac Python3.9でprocess間のmonotonic原点を共通と仮定しない。UTC順序は今回の同一Mac観測であり、分散clock同期の保証ではない。

実client timeoutはsocket待ちのtimeoutで、接続/実行overhead込みの総時間をちょうど2秒へ制御するend-to-end timerではない。attempt02のslowは実観測待ち約2005.63ms、status/body未受信。serverはその後200を生成して送信を試み、WRITE_RETURNEDを記録したが、client配送成功とはしない。BrokenPipe/connection resetならSEND_ERRORをそのまま保存する。今回それらは観測されなかった。

初回attempt01はPython3.9のsocket.timeoutを一般transport errorへ誤分類した。原票と旧sourceを保持し、型分類を修正したattempt02でCLIENT_TIMEOUTを再確認。初回を成功へ書き換えない。2attempt各2requestは例示で、性能、p95、一般SLO、品質全体の推定ではない。UIの「保存実HTTPを読む」は再実行せず、模型と別panelへ表示する。

## 再現

既存Mac Python3.9.6標準ライブラリとBrowserのみ。依存install、課金、OS/driver/Docker/権限設定変更なし。

```sh
python3 -B model.py
python3 -B verify.py
python3 -B route.py
python3 -B serve.py
```

server表示の127.0.0.1動的portで入口を開く。予想→模型操作→正常/境界/拒否→保存実HTTP→原典/source/raw→答え。予想/入力変更でticketを進め、旧result/answer/raw/trace/summaryを消し、新しい予想を保持する。保留旧応答は破棄。入力拒否、transport failure、timeoutという測定結果を区別する。所有server/tabのみ終了。

通常verify/routeは模型を再計算し、保存実HTTP/receiptを読むだけで、実HTTPを再実行しない。明示原票記録は未使用attemptに限定。制作で実行済みの `python3 -B actual_http.py --record http-attempt-01` / `http-attempt-02` は同名再実行を拒否する。[独立oracle](oracle.py)はmodel/harnessをimportせず事前literal表・request ID・実raw列・UTC順序を照合。12模型条件、7入力拒否、6mutant、nearest-rank20件の例、初回/修正版実HTTPを検査する。

source/artifact hash、UTC/runtime、raw、UI QA、capture保存可否、所有resource cleanupをobservationsへ保存。[有限Skill](skills/qe-atlas/SKILL.md)はこの入口と最初の教材に限定し、未教材章を実証済みとは扱わない。独立Agent理解度評価は未実施。

## 原典

[Google SRE Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) Indicators / Collecting / Aggregationは、利用者に関係するSLIとclient/server観測、平均で隠れるtailの入口。[NIST Percentiles](https://itl.nist.gov/div898/handbook/prc/section2/prc262.htm)は標本分位点の方式差、[NIST Experimental Design](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3.htm)は実験計画の入口。[NIST Taguchi designs](https://www.itl.nist.gov/div898/handbook/pri/section5/pri56.htm)は制御/noise因子を分けたparameter designとtolerance designを扱う。今回のHTTP行列はTaguchi/SN比/直交配列/因果実験ではない。

専有pathだけを新規制作。既存Subject/continuation/GPU/Portal/Core/global docs/registryは未変更。Core/full gate・公開・commit/pushは範囲外で未実行。入口と1教材の凍結であり、全QE Atlas完成とはしない。

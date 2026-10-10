# 検知・対応・forensicsを学ぶ入口

Macの標準Pythonだけで、公開の架空固定JSONログを処理する有限1教材です。実アカウント監視、攻撃、実端末forensics、実ログ収集は行いません。Docker・外部サービス・追加依存は不要です。このSubject全体や全97分野の完成ではありません。

## 前提 → 主要概念と仕組み

JSON、整数時刻、集合、件数を前提にします。ログの発生時刻（event time）と入力位置（arrival index）は別の情報です。同じmock userの成功時刻tに対して、`t-window <= failure.time < t` の失敗がthreshold件以上あればalertを返す、教材独自のルールを使います。既定は3件/30秒。NISTが指定する閾値ではありません。

ログをschema検証→idで重複排除→順序決定→時間窓評価→decision chain保存へ通します。整数以外のtimestamp（booleanも含む）、未知user/action、余分/不足fieldを拒否します。重複idの同一内容は一度だけ数え、内容が矛盾するidは処理全体を拒否します。JSON全体の壊れた構文はfixture読込エラーです。黙って成功扱いにしません。

成功130の窓は[100,130)：100は含み130の失敗は「前」でないため除外。別userの失敗は数えません。event time方式は有限batchを `(time,id)` で整列します。naive到着順方式は成功を見た時点で既に到着した失敗だけを数え、後から届いた失敗で再評価しません。成功ごとに評価し、失敗のresetやalertの抑制はしないモデルです。

## 今回の実装 → 正常・境界・意図異常

このディレクトリで実行します。`-B`はbytecode書き込みを抑止します。

```sh
python3 -B run.py --case normal
python3 -B run.py --case late --mode arrival
python3 -B run.py --case late --mode event-time
python3 -B run.py --case boundary --window 30
python3 -B run.py --case boundary --window 29
python3 -B run.py --case duplicate
python3 -B run.py --case invalid
python3 -B check.py
python3 -B server.py
```

serverが表示する動的127.0.0.1 URLで [index.html](index.html) を開きます。止めるときは自分のserverへCtrl-C。CLI [run.py](run.py) とHTTP [server.py](server.py) は [model.py](model.py) の同じ実処理へrouteします。固定入力は [fixtures.json](fixtures.json)。任意の実ログを取り込む入口はありません。

画面は **予想→操作→比較→原典/実装→答え** の順です。ケース、処理順、窓、閾値を操作して、2本の実processing order、alert id、独立oracle、実input hash、decision chainを見比べます。全原票の折りたたみを開くと実input、正規化記録、拒否/重複、decision chainとdigestが見えます。

| 固定case | 既定event time / 到着順の期待 | 比較の問い |
| --- | --- | --- |
| normal | alert / alert | 3失敗後の成功を検知できるか？ |
| late | alert / なし | 成功が先着すると何を見逃すか？ |
| boundary | alert / alert | 下限100は含むか、同時刻130は除外か？ |
| outside | なし / なし | 99は窓外か？ |
| duplicate | なし / なし | 重複を件数に足すと誤検知になるか？ |
| invalid | なし / なし | 型不正を黙って変換していないか？ |
| other-user | なし / なし | 別userの失敗を混ぜていないか？ |

[oracle.py](oracle.py) はmodelをimportせず、成功ごとに入力集合を直接走査して時間差とarrival indexで数えます。既定7ケースには独立した手計算期待表も置きます。[check.py](check.py) は7case×3窓×3閾値×2順序の126比較、全24到着順の両方式48比較、型・範囲・矛盾重複の拒否、意図的な境界/重複の壊れたモデルを検査します。異なるagentの評価や形式的証明ではありません。

通常checkerはread-onlyです。原票更新は明示option `python3 -B check.py --record` だけ。[evidence/run.json](evidence/run.json) に実行時刻・環境・input・正規化・decision chain・raw/digestを保存し、[evidence/bindings.json](evidence/bindings.json) でsource/artifactをSHA256結合します。画面の通常操作は計算結果を表示し、原票のファイル更新はしません。今回の実IAB HTTP QAは10ケース成功し、title/fields、拒否原票、答え、roadmapを確認しました。実full-page JPEG captureは取得・tool表示・目視確認済みですがmoduleへ未保存です。再描画ではありません。captureファイルの永続保存は未検証です。自分のserver/tabは終了済み。[evidence/ui-qa.json](evidence/ui-qa.json) は実IAB QAとcaptureの保存可否を区別します。

## 今回判断できること → 実務判断と限界

到着順の正しさを仮定すると見逃す理由、時間窓の包含条件、重複排除の必要性、正規化拒否を証拠に残す意味を説明できます。alertはルール一致であり侵害の確定ではありません。正常な利用者の入力ミスでも同じパターンが起き得ます。実務へ進むには、誤検知/見逃し、収集欠落、clock skew、保管権限、調査範囲、対応承認の判断が必要です。

input hashは同じbytes/値の比較に使い、出所・真正性・chain of custodyを証明しません。実forensic収集、保全、証拠の法的評価は未実施。有限batch整列は無限streamのwatermark、遅延許容、再評価、メモリ境界を実装していません。実認証プロトコル、SIEM/EDR連携、自動隔離、侵害判断へそのまま転用できません。

## Subjectの主要未教材coverage → 次の4実験

| 未教材の概念・問い | 次に作る実験（未実装） | 公式locator |
| --- | --- | --- |
| telemetry設計・時刻同期・収集欠落・保持・アクセス：観測なしと出来事なしを区別できるか？ | 架空source2本のclock skew/欠落/遅延とwatermarkを比較 | NIST SP 800-92（ログ管理） |
| 検知工学・baseline・相関・脅威ハンティング・精度：閾値を変えると誤検知はどう変わるか？ | 架空ラベル付きログでprecision/recallと閾値を比較 | SP 800-61 Rev.3（Detect） |
| triage・severity・封じ込め・根絶・復旧・事後改善：どの証拠でどの対応へ進むか？ | 架空incident状態機械で判断条件と復旧確認を比較 | 同原典（Respond / Recover） |
| forensic収集・保全・examination・analysis・報告・chain of custody：hash一致だけで真正性を言えるか？ | 架空証拠の複製/改変/引渡し台帳を比較 | SP 800-86 §3、§4.2.2 |

SIEM/EDR、実disk/memory/network取得、malware解析、実監視・封じ込め、脅威intelligence、分散stream、証拠の法的評価は未教材・未検証です。上記は次の候補であり、今回着手しません。

## 原典へ戻る

- [NIST SP 800-92](https://csrc.nist.gov/pubs/sp/800/92/final)：ログ管理・分析を学ぶ入口。正規化、時刻の扱い、収集・保持のcoverageへ結合。この教材の閾値を規定するものではありません。
- [NIST SP 800-61 Rev.3](https://csrc.nist.gov/pubs/sp/800/61/r3/final)：検知・対応・復旧をrisk managementへ組み込む枠組み。alert後の判断と未教材coverageへ結合。
- [NIST SP 800-86](https://csrc.nist.gov/pubs/sp/800/86/final)：§3 forensic過程、§4.2.2 integrity、§5–8データ源と分析。教材のhashと真正性の限界・次の実験へ結合。

locator確認日：2026-10-05。SP 800-92の出版ページは確認、PDF取得はtimeoutで未確認。他2資料は出版ページ/PDFを確認。source bindingは原典と教材の対応であり外部内容の完全ミラーではありません。

## Skillと検査範囲

[SKILL.md](skills/atlas-detection-response-forensics/SKILL.md) はこの既存runner/checker/UIへ限定routeします。[evidence/routing-smoke.json](evidence/routing-smoke.json) は正常/未対応要求のmain-agent routing smokeであり独立forwardAgentEvalではありません。

対象module外の検査・編集は禁止です。repo全体の `npm run gate`、Core audit、repoctl admission verify は未実行。module検査をrepo全体gate成功やcommit可能性、全Subject完成と扱いません。

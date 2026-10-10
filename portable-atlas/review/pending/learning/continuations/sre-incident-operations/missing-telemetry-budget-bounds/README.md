# seen-only 100%でも、全台帳の予算は範囲になる

[既存multiwindow](../multiwindow-burn-alert/README.md)のmissing/late次案を進める有限続編。[collector欠落教材](../../observability-engineering/collector-missing-late-quantiles/README.md)の独立発行台帳と未知品質を参照するが、旧コードを動的に呼ばず変更しない。前提は分母、Fraction、cutoff、未知、error budget/burn。

tick0に全IDを発行した合成台帳からeligible Nを知る仮定。見えた3goodだけならseen-only100%、台帳N4で1unknownならtarget4/5の達成は判定不能。late bad到着で範囲が縮まり未達に確定する。未観測をsuccess/failureへ埋めず、best/worst残予算とburnを出す。台帳完備・配送・request品質は実pipelineから保証された事実ではない。

予想→cutoff/台帳/観測/target操作→実Python計算→状態と範囲図/手表→[原典](SOURCES.md)→source/raw→答え。[契約](EXPECTATIONS.md)の等値包含、N0、target100% burn未定義を先に読む。

~~~sh
python3 -B runner.py
python3 -B runner.py seen-only-100-unknown
python3 -B runner.py late-bad-arrives
python3 -B checker.py
python3 -B test_negative.py
python3 -B server.py
python3 -B runner.py --record
python3 -B checker.py --record-binding
~~~

専用dynamic127.0.0.1、memory-only server。UIは実model/別oracle子processと同request receiptを照合、JSで予算判定を再計算しない。通常CLI/再試験はファイルを変更せず、recordだけ新UTC/UUID rawと成功currentを保存、旧失敗を保持。模型はtmp fileを作らない。終了は自分のterminal Ctrl-C/owned tabのみ。

[fixture](fixture.json) · [手答え](oracle.json) · [編集手答え](custom-oracle.json) · [current](evidence/current.json) · [実IAB QA](evidence/browser.json) · [検証](evidence/verification.json) · [Coverage](COVERAGE.md) · [有限Skill](skills/atlas-telemetry-budget/SKILL.md)

未教材: 実collector/ledgerの完全性、配送保証/永久loss判定、重複/訂正/分散clock/stream、確率推定/欠測補正、実pager/目標妥当性/本番SLO判断/Safety/人の承認。次は独立台帳自体の欠落と補正receiptを分ける有限単位（未実施）。Core/global/QE/Portal/registry/旧unit/設定/install/公開/commit/push/他owner資源は変更せず全分野完成を主張しない。

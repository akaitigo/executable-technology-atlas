# actionを完了しても、有効性はまだ未確認

[既存SRE入口](../../../subjects/sre-incident-operations/README.md)のpostmortem/action再試験へ進める有限続編。架空INC-DOUBLEの根拠→ACT-DOUBLE→bad/部分修正/修正版の実Python再現・regressionを比較する。前提は要求、source digest、test PASSとaction doneの違い。

badは誤答と期限無視、部分修正はREPROに通っても等値EQUALで失敗、修正版は手oracle7条件に一致する。旧fixed-v1の実PASSは現在fixed-v2の有効性証拠にならない。action完了だけならUNVERIFIED。実試験結果とsource/version、完全suiteを結び付けてVERIFIED_FINITEを出す。

予想→条件→実Python再試験→action/proof/失敗境界図と表→[手表](EXPECTATIONS.md)→[一次資料](SOURCES.md)→build source/実子process raw→答え。logical ticksは合成cost、実応答性能/本番復旧の観測ではない。人の承認・本番有効性はUNCONFIRMED。

~~~sh
python3 -B runner.py
python3 -B runner.py partial-retest
python3 -B runner.py stale-build-pass
python3 -B checker.py
python3 -B test_negative.py
python3 -B server.py
python3 -B runner.py --record
python3 -B checker.py --record-binding
~~~

serverは専用dynamic127.0.0.1でmemory-only、UI比較は実modelと内側build test子process、別oracle、同request receiptを照合しファイルを書かない。通常runner/checkerはread-only、明示recordだけ新UTC/UUID rawを保存。旧原票を保持。終了は専用terminal Ctrl-C/owned tabだけ。模型はtmp fileを作らない。

[fixture](fixture.json) · [tests手oracle](tests.json) · [手答え](oracle.json) · [編集手答え](custom-oracle.json) · [current](evidence/current.json) · [実IAB QA](evidence/browser.json) · [検証](evidence/verification.json) · [Coverage](COVERAGE.md) · [有限Skill](skills/atlas-incident-action/SKILL.md)

未教材: 実本番incident/根因/CAPA監査、長期署名proof、人の承認、deployment/rollback、実latency・利用者影響、巨大regression/全品質/Safety/SLO、因果一般化。次は架空変更のrollout/rollback根拠と本番観測を分ける単位（未実施）。Core/global/QE/Portal/registry/旧教材/他owner資源/設定/install/公開/commit/pushを変更せず全分野完成を主張しない。

evidence_buildの旧baseline試験も今回の操作時に実再実行し、別versionのPASSとして比較する。歴史的な本番観測や以前保管された署名原票を生成するものではない。

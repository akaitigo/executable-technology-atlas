# 速くても誤答、正しくても遅延: 受入ANDとParetoを分ける

[既存Requirements入口](../../../subjects/requirements-engineering/README.md)の架空needs/測定条件を有限データで比較する独立続編。専有directoryのみ。前提は要求ID、正答数、締切、AND、支配/非支配。

架空用途「3件の既知応答を正しい内容で期限内に受信」で、N-FAST→R-TIMELY、N-RIGHT→R-CORRECTを明示。Aは速い誤答、Bは正しい遅延、Cは両方合格、Dは劣る、E/Fは不足/未観測。閾値を変更しても正しさと時間をweighted scoreで相殺しない。Pareto集合は候補比較、受入は要求AND判定で別である。

予想→条件/閾値/観測data編集→実Python評価→旧新受入表/Pareto図→[契約手表](EXPECTATIONS.md)→[原典](SOURCES.md)→source/raw→答え。数値は合成fixture、PC/ネットワーク/製品の実測性能ではない。Python evaluatorは実行するが製品testや観測取り直しではない。人の承認/実利用validationは常にUNCONFIRMED。

~~~sh
python3 -B runner.py
python3 -B runner.py fast-wrong-correct-late-both-missing
python3 -B runner.py both-relaxed
python3 -B checker.py
python3 -B test_negative.py
python3 -B server.py
python3 -B runner.py --record
python3 -B checker.py --record-binding
~~~

serverは専用dynamic127.0.0.1。UIは実model＋別oracle子processと同request memory receiptを照合し、通常実行はファイルを更新しない。停止は自分のterminal Ctrl-C/owned tabだけ。明示recordは全24条件を新UTC/UUID原票に保存し成功だけcurrentへ昇格、旧失敗も保持。模型はtmp fileを作らない。

[fixture](fixture.json) · [手答え](oracle.json) · [編集手答え](custom-oracle.json) · [current](evidence/current.json) · [実IAB QA](evidence/browser.json) · [検証](evidence/verification.json) · [Coverage](COVERAGE.md) · [有限Skill](skills/atlas-quality-acceptance/SKILL.md)

未教材: 実利用者needs決定、閾値妥当性/合意、実計測/分布/信頼区間、欠測原因、実利用validation/承認、品質特性全体/Safety/SLO/製品完成。次は実測データと用途validationを別記録する有限単位（未実施）。全分野完成を主張せずCore/global/Portal/QE/registry/旧教材/設定/install/公開/commit/pushを変更しない。

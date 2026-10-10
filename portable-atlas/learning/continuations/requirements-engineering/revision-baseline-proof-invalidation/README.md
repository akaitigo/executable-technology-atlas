# graph到達と旧PASS証拠を別々に失効させる

[前の双方向影響](../bidirectional-change-impact/README.md)の次案2だけを進める。6ノード・2枝のrevision metadata模型。旧/new到達graphと、test証拠に保存されたbaselineを別比較する。前提はID・有向edge・revision・SHA-256・旧PASSと現在証拠の違い。

要求revision変更は旧graph cacheと当該proofを失効させる。test実装revisionだけの変更はgraphを変えずproofだけ失効。link削除は残るgraphを計算できてもUNKNOWN_TRACE。未影響枝のproofは保持できる。要求内容hashが同じでもrevision変更は失効、同revision/hashの対照や順序変更だけなら失効しない。全て独自の有限契約で、実製品の精密影響を保証しない。

予想→条件→実Python metadata処理→旧新到達/impact・proof失効図→[契約/手表](EXPECTATIONS.md)→[原典](SOURCES.md)→source/raw→答え。new graphの再計算を実test再実行と呼ばない。stored PASSは合成fixtureの宣言で、今回新しいtest PASSを作らない。実test実行false、人の承認UNCONFIRMEDを常に表示する。

~~~sh
python3 -B runner.py
python3 -B runner.py requirement-revision
python3 -B runner.py test-revision
python3 -B checker.py
python3 -B test_negative.py
python3 -B server.py
python3 -B runner.py --record
python3 -B checker.py --record-binding
~~~

専用serverはdynamic127.0.0.1 URLを表示する。各UI比較は実model子process＋別oracle子process、同request IDのmemory receiptを照合。JSでgraph探索やproof判定を再実装しない。通常CLIはread-only、明示recordのみ新UTC/UUID raw＋current更新、旧失敗も保存。純粋metadata計算はtmp fileを作らずserverもmemory receiptのみ。終了は専用terminal Ctrl-Cと自分のtabだけ。

[fixture](fixture.json) · [固定手答え](oracle.json) · [編集手答え](custom-oracle.json) · [current](evidence/current.json) · [実IAB QA](evidence/browser.json) · [検証](evidence/verification.json) · [有限Coverage](COVERAGE.md) · [Skill](skills/atlas-revision-proof/SKILL.md)

未教材: 実test再実行、要求獲得・妥当性、実製品graph完全性、stakeholder変更承認、一般多対多/循環、semantic diff、署名/偽造耐性、SLO/Safety/製品完成。次は選択testの実再実行と人の変更審査を別記録する有限単位（未実施）。Core/fullGate/Portal/global/registry/QE/旧教材/設定/install/課金/公開/commit/pushを変更・実行せず、Subject/Atlas完成を主張しない。

Cross枝では現在ancestor所属の全枝canonical関係を保守的に要求する。別testへのlink欠落でも当該ancestor枝が不完全ならUNKNOWN_TRACEとなる。詳しくはEXPECTATIONS.md末尾。

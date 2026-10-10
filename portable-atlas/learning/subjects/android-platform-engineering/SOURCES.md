# 公式contractのlocatorと実装binding

確認日2026-10-05。以下3文書はWeb本文を取得確認。引用コピーではなく、この教材の仮定/問いを紐付ける。今回実行したのはPythonの有限modelだけでAndroid SDK/device/emulatorは未実行。

| ID / 公式資料と節 | 今回の対応 / 限界 |
|---|---|
| ACT [Activity lifecycle (Views)](https://developer.android.com/topic/libraries/architecture/views/activity-lifecycle-views), lifecycle callbacks / instance state / save and restore | create/start/resume/pause/stop/destroyの概念、onSaveInstanceState→onCreateの小さな復元を[model](model.py)で表す。rotationによるinstance再生成を[手記](handtrace.json)と比較。callback scheduling/API差/実Bundle/View hierarchyを実装していない。 |
| STATE [Save UI states (Views)](https://developer.android.com/topic/libraries/architecture/views/saving-states-views), options table / system-initiated destruction / user dismissal | ephemeral、saved snapshot、永続storageの寿命を分ける学習。小さなUI stateだけ対象。ViewModel/registry/Room/Compose未実装。finishは保存recordも消すmodel分岐。 |
| PROC [Processes and app lifecycle](https://developer.android.com/guide/components/activities/process-lifecycle), cached processes / onDestroy caveat | process deathでonDestroyを付け足さない。snapshotあり/なし/古い/利用不能を別case化。OS killer/実process優先度の再現ではない。 |
| MODEL [有限契約](SPEC.md), event table / codec / assumptions | counter0..9、JSON128byte、MAX32、explicitsave/drop_savedは作者の有限化。[independent oracle](oracle.py)は別transition table/save tokenから両variantを検査。Android自体の証明ではない。 |

次の4実験の公式locatorは[COVERAGE](COVERAGE.md)。未取得locatorはそこで明記。最新Compose-firstの[Activity guide](https://developer.android.com/guide/components/activities/activity-lifecycle)と[Save UI states](https://developer.android.com/topic/libraries/architecture/saving-states)も本文確認したが、今回はViews callbackを説明する有限modelでありComposeアプリではない。

[入力](cases.json)→[保存原票](evidence/raw.json)→[実行時刻/環境/digest](evidence/run.json)→[artifact binding](evidence/integrity.json)。source/input/raw/図/実IAB画像はSHA-256で固定。原典は保証範囲を知る資料、modelの実行証拠とは別。

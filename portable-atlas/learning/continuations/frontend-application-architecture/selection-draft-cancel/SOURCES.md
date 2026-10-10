# React原典とvanilla JSの独自契約

2026-10-05に[React Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)本文を確認。ReactがUI tree内の位置/identityでstateを関連付け、identity変更でresetを制御する概念を、selectionとdraftの所有を考える入口として読む。

今回の実装はvanilla JSの独自ID別draft mapで、React component/keyを実行していない。切替時保持/cancel対象/save対象は[事前契約](EXPECTATIONS.md)へ明示し、公式挙動と同一視しない。原典のUI/codeを複製していない。

[実DOM producer](app.js)、[手書きID表](oracle.json)、[独立検証](oracle.py)、[current raw](evidence/current.json)へ戻り、実Browser DOM/URL/inputの観測とモデルのlogを照合する。URL選択はown tab内historyで、製品router、reload後保存、network/persistence保証は未実証。

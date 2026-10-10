# 収束しても予約上限は守れるか

在庫1をpartition中のA/Bがそれぞれ受理すると、union後は同じ2件に収束してもaccepted≤1を破る。保留の対照ではpendingを明示して復旧後に固定順で判定し、1件accepted・他rejectedとなる。受理済みの応答は同期で取り消さない。

```sh
python3 -B server.py --port 0
python3 -B runner.py
python3 -B route.py baseline
python3 -B checker.py
```

serverが表示した127.0.0.1 URLを開く。予想を入力し、ケースを選び、容量・要求・判定順・配送順をJSONで変更して実行する。両方針の全trace、利用者応答、集合図を比較し、原典と実装へ戻り、答えを読む。入力編集/ケース変更/resetは古い答えを消す。保留した旧結果の表示操作は、編集後に古い応答が無視されることを試す。503は実routeの失敗である。

[契約](EXPECTATIONS.md)、[手表](hand-trace.json)、[独立oracle](oracle.py)、[coverage](COVERAGE.md)、[原典](SOURCES.md)、[Skill](skills/atlas-reservation-invariant/SKILL.md)。モデルの集合図は計算結果を描画した説明図で、実networkの図ではない。native画像は実ブラウザの静止画。

入力は2 replica、capacity0〜3、異なる予約ID最大4件、明示配送最大6件。空や片方向scheduleは未配送のまま終わる。一致がtrueでも必要情報の到達を意味しない。有限scheduleの全検査は2通全2順＋重複4通全24 positional順（8 unique）。任意の配送/故障一般の証明ではない。

Lamport p.559は並行eventの根拠のみ。直列判定器とunionは本教材独自の規則。global stepは再生順であり、A/B request間の因果edgeにしない。実通信・CRDT・CAP・consensus・取消補償・実予約・linearizabilityは検証しない。Subjectの学習文書は参照用で、計算はこの候補だけで動く。global gate/公開は未実行。

rawを更新する明示操作は`python3 -B runner.py --record`、通常CLI/checker/routeはファイルを書かない。

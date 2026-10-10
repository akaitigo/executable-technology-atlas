# 配送順と2 replicaの一致を比べる

partition中の並行書込み、復旧後の到着順上書きの反例、論理versionのmax mergeによる収束を、標準Pythonで実計算する1教材です。実ネットワーク、データベース、consensusの試験ではありません。図・UIは計算したraw eventを再生します。

## 起動と検査

このmoduleディレクトリで実行します。追加依存なし。今回の実行はCPython 3.9.6 / Darwin arm64。新規環境は保守中のPythonを推奨しますが、その版での追試は未実施です。

```sh
python3 -m unittest -v test_model
python3 model.py --record
python3 serve.py
```

`http://127.0.0.1:18772/`を開きます。サーバー終了はCtrl-C。loopbackはUI→Pythonにだけ使用し、A/B replica間通信はPython内部のmessageオブジェクト操作です。Dockerや追加のnetworkは作りません。

`model.py --record`は入力、書込み集合、queue、全event/state、delivery、最終結果、全6順のOracle比較、Python版、UTC時刻、command、実装SHA256を`observations/comparison.json`へ保存し、同じJSONをstdoutに出します。再実行はCLI原票を置換するので、旧結果を残す必要があれば先に別名で保管してください。UIの各計算は固有名`observations/ui-*.json`に保存されます。検査を記録する場合は`python3 test_model.py --record`（原票`observations/tests.json`と`tests.txt`）。

## 予測 → 操作 → 比較 → 答え合わせ

1. 「復旧して全部届けば、両ruleとも同じ値になる？」と予測する。
2. 配送順A2,A1,B1で「Pythonで比較」。左の到着順上書きはA=beta、B=alpha。右のversion maxは両方alpha-2。
3. 「partition中の書込み後」へ戻すと、両ruleともA=alpha-2、B=beta。リンク復旧直後もまだ異なる。復旧と全message配送を区別する。
4. 配送順B1,A1,A2へ変える。duplicateなしの到着順はA=beta、B=alpha-2となり、Bの最終値は配送順に依存する。maxの両値は変わらない。
5. 「最後に古いA1を再配送」を有効にする。arrivalのBはalphaへ戻るがmaxのBはalpha-2を保持。
6. event slider、原票、[実装](model.py)、[checker](test_model.py)、原典の該当箇所で答え合わせする。

## モデルの契約

- 2 replica / 1 register、初期値∅。Aのlocal write/sendはalpha (1,A)、alpha-2 (2,A)、Bはbeta (1,B)。partition中の配送は拒否する。
- local write/sendでcounter+1。receiveでmax(local counter, message counter)+1。versionは**書込み時**の(counter, replicaID)で、受信clockへの再labelはしない。
- counterを先に比較し、同値ならreplicaID（A<B）。到着順ruleは無条件上書き。max ruleは大きいversionだけを採用し、同一versionは保持する。
- 全3 messageが両replicaへ反映されるまで届ける。messageはimmutableな書込みsnapshotで、同じIDを再配送できる。永久loss、crash、membership変更は扱わない。
- 教材のglobal stepはイベント再生順。A/B間の因果関係や物理時間を新たに作るものではない。

独立Oracleは`deliver()`を使わず、全書込み集合をsortして最大labelを得ます。固定3 messageの全6順ではmaxは6/6 Oracle一致、arrivalは0/6 register一致。duplicateを含む24 positional permutations（重複を除くと12順）とdelayed stale、同counter tie-breakも検査しています。9 unit検査が成功し、全eventが決定的なことも確認しました。

この有限列挙と、max演算の交換・結合・冪等性からのモデル内説明を、任意システムの全実行検証へ拡張しません。片方へmessageが永久に届かなければ収束条件を満たしません。

## 原典との関係と境界

[Leslie Lamport, *Time, Clocks, and the Ordering of Events in a Distributed System*, CACM 21(7), July 1978, 558–565](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/12/Time-Clocks-and-the-Ordering-of-Events-in-a-Distributed-System.pdf)を2026-10-05 JSTに閲覧しました。

- 刊行p.559 / PDF p.2「The Partial Ordering」「Logical Clocks」：happened-before、並行、counterとphysical timeの区別。
- 刊行p.560 / PDF p.3「Clock Condition」「IR1/IR2」：因果順序に沿うclock条件、逆は成立しないこと、受信時のclock更新。
- 刊行pp.560–561 / PDF pp.3–4「Ordering the Events Totally」：clock値とprocess順序でtie-break。

原典本文・図は保存／複製しません。本教材は論理時計を利用した独自max-registerで、論文の相互排他algorithmやphysical clock同期を実装したものではありません。シミュレータコードの版は各原票のSHA256で固定します。

logical labelは実時計でも因果関係そのものでもありません。A2とB1は並行ですが(2,A)>(1,B)と便宜的に順序づけます。このLWWに似た選択は最終registerからalphaとbetaを失います。収束しても在庫、残高、予約などの業務invariantは保証しません。partition中のlocal writeの継続と一時的不一致を観測しても、CAPを一般に実証したとは扱いません。

Subject全体の未教材領域と他Subjectへのcredit 0は[coverage.json](coverage.json)に明記しています。consensus、linearizability、vector clocks、durability、実transport、transactions、CRDT全範囲、安全なproduction導入は未対応です。

## 観測と再利用

- [CLI原票](observations/comparison.json)
- [QA・画面・Skillの確認](QA.md)
- [module内Skill](skills/atlas-distributed-systems/SKILL.md)

これは今回1教材の実装・観測結果です。旧Argo/Core/Definitive作業、Subject全体の完成、全69分野の教材完成、global Skill install、GitHub公開を意味しません。

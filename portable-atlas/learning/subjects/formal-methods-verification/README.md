# Formal methods: mutexの最短反例を歩く

空き確認と入室を1つの原子的stepにすると相互排他は守られるか。確認だけを先に済ませ、入室のguardを取り去ると、どの順序で破れるか。2 processの独自state machineを標準Pythonで全到達状態探索し、ブラウザで反例を操作する教材です。

## 予想 → 操作 → 比較

1. [index.html](index.html)の「予想する」で回答を選ぶ。
2. 「欠陥の最短反例を見る」→「次の反例step」を順に押す。
3. 両者のpcが`ready`になったときのownerと、後で両者が`critical`になる状態を比べる。
4. 正常モデルへ切り替え、P0を入室させた状態でP1の入室操作が存在するか確認する。
5. 「全到達状態」から各状態の許されるtransitionを確認する。

今回のPython実観測は正常8状態/14遷移/違反0、欠陥23状態/44遷移/違反2、最短反例6遷移です。最短traceは初期状態を含め7状態で、BFSが作った親edgeを逆にたどって抽出しています。探索は違反発見後も続け、到達集合が閉じるまで全edgeを列挙します。

## このMacで再現する

依存はPython 3.9以上の標準ライブラリだけです。Repository rootから:

```bash
cd learning/subjects/formal-methods-verification
python3 -B observe.py
python3 -B verify.py
python3 -m http.server 8796 --bind 127.0.0.1
```

ブラウザで <http://127.0.0.1:8796/> を開きます。サーバーは`Ctrl-C`で停止します。`index.html`を直接開いても同梱`data.js`を読めます。Docker/Node/npm/TLC/Leanは不要です。

`observe.py`は新しいPython subprocessで`check.py`を実行し、生stdoutと実行時刻・環境・input・source digestを保存します。ブラウザは保存された探索結果を表示し、そのtransitionだけを操作します。UI内の操作自体がPythonを再実行するわけではありません。観測更新後はページを再読込してください。

## 一次資料 → 実装 → 答え

- [LamportのPlusCal tutorial / Mutual Exclusion](https://lamport.azurewebsites.net/tla/tutorial/session8.html): 相互排他、不変条件、atomic step、機械実装への注意。
- [同 / Liveness](https://lamport.azurewebsites.net/tla/tutorial/session9.html): safetyだけでは進行を保証できず、schedulerのfairnessが関わる。
- [Python公式 / deque](https://docs.python.org/3/library/collections.html#collections.deque): FIFOでBFS frontierを管理。
- [model.py](model.py): `State`・`successors`・`invariant`・到達状態BFS。
- [evidence/stdout.json](evidence/stdout.json): 今回のcheckerの生stdout（全状態、全transition、最短反例）。
- [evidence/run.json](evidence/run.json): source version、観測時刻、環境、command、input、stdout digest。

答えは「guardを評価した状態と、入室を書き込む状態が離れると、途中で前提が変わりうる」です。正常モデルではcheck-and-enterが1つのatomic stepなので、この割込みがありません。実装にそのatomic性があるかは別のrefinement検証です。

## 観測範囲

これは抽象モデルを実際に実行した記録で、OS threadのmutex実測ではありません。任意の時間長の実行は、有限到達state graphのcycleとして表現されます。深さ上限はありませんが、process数と値domainは有限です。

Safetyはすべての到達状態で検査しました。Livenessの時間的性質は未検査です。公平性なしなら、P1をwaitingに置いたままP0だけがrequest→enter→releaseを繰り返す実行が許されるため、safetyから「必ずP1が進む」とは言えません。詳細は[COVERAGE.md](COVERAGE.md)。

この教材単位はローカル保存。分野全体の知識網羅・理解度・既存Atlasの完成状態は更新していません。画面QAは[evidence/visual-qa.json](evidence/visual-qa.json)へ記録します。

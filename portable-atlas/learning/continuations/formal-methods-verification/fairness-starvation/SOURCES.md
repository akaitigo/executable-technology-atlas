# Atlas：公平性の原典と独自モデル

Lamport 著者本文 [Session 9: Liveness](https://lamport.azurewebsites.net/tla/tutorial/session9.html) §5 Semaphore Liveness と§6を2026-10-06に読みました。ページには最終更新2024-08-19の表示があります。弱公平性の継続enabled、強公平性の無限回enabled、状態を変えない停滞を進行に数えないことを参照します。進行性は時間上限とも区別します。本文の全複製やTLCの実行は行っていません。

Atlasでは、旧独自mutexの `atomic` 動作を使い、`Next_i = request_i ∨ enter_i ∨ release_i` を process の対象として固定します。idleのrequestも対象です。これは原典の任意の `fair process` 宣言や非critical区間の例外と同じものではありません。

prefix後にcycleを反復する6列、cycle内のall/anyによる判定、P1.enterだけの強公平性とprocess弱公平性の組合せは [今回の契約](CONTRACT.md) です。有限に保存した一周を数学的に無限反復する説明で、無限時間を実測した証拠ではありません。

既存の正常モデルは [完全一致コピー](inputs/prerequisite-model.py) と [hash/出所](records/input-and-dedup.json) へ。新しい計算や図が、そのモデルを実装へ写す証明になったとは扱いません。

## Atlas の実装への対応

|原則|今回の適用先|読取りの限界|
|---|---|---|
|弱公平性の継続した実行可能性|`fairness.py` の `analyze`：cycle の all(enabled) と any(executed)|有限周期列への簡約であり、任意列の判定器ではない|
|強公平性の繰り返す機会|同じ関数の any(enabled) と any(executed)|Enter1だけを対象にした仕様はreleaseを含まない|
|停滞と進行動作の区別|`edges` はstutterのprocessをnullへ|非停滞辺の実行と同一視しない|
|要求の後の入室|`progress_obligations` は順序を保つ|過去のcriticalを後のwaitingへ流用しない|

元モデルの `successors` は入室を `check-and-enter` と命名しています。今回だけ `P0.enter / P1.enter` と表示し、保存値の `source_event` に元の動作名を残します。元の14辺や原子性の意味は変えません。版と元ファイルSHA-256は [出所記録](records/input-and-dedup.json)、計算に用いた全入力のSHA-256は状態記録から辿るrunへ保存します。

著者本文の読了箇所と取得状態は [source-read.json](records/source-read.json) にあります。URLの存在や資料索引を本文意味確認と同一視せず、上の規則と独自モデルへの適用を分けます。

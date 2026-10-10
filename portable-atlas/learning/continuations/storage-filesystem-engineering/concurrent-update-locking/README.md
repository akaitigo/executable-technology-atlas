# renameだけで、2人の更新を守れる？

[第1単元](../../../subjects/storage-filesystem-engineering/README.md)で見たwrite-new/replaceは、途中でtruncateしたbytesを公開する問題を避ける。しかし複数writerが同じ旧値を読み、別々に新版を作れば更新が消える。この追加単元は既存COVERAGEの次2を、Macの実2process・実temp filesで深掘りする。原入口や原票は変更しない。入口数97に加算せず、全Subject完成も主張しない。

前提はpathとopen FD、rename、read-modify-write、process間の順序。仕組みは「完成したbytesへの切替」と「旧値を読むところからcommitまでの排他」の違い。共有設定counterを初期0、A/B各+1とする。

| 実ケース | 制御する順序 | 独立期待値 | 実務上の意味 |
|---|---|---|---|
| replace-only（意図異常） | A/Bとも0をread、各1を別candidateへwrite、A/B順rename | 0→1→1、最終1 | bytesは完全でもAの更新は消える |
| stable-lock（正常） | A取得、B取得はwould_block、A read/rename/release、B取得/read/rename/release | 0→1→2、最終2 | 協力するwriterの更新全体を直列化 |
| abort-before-commit（境界） | A candidate完成後abort/release、Bは0から更新 | 0→0→1、最終1 | abortした更新は反映しない、解放後に進める |

[UI](index.html)で **予想→操作→比較→原典/実装→答え**。各eventを送り、PID・lock取得/拒否/解放・read/write/renameとcheckpoint bytesを追う。UIは保存した実runの再生で、browserからprocessを起動しない。手順はpipe応答barrierで固定し、Bの競合は実 `fcntl.flock(LOCK_EX|LOCK_NB)` で観測する。sleepによる確率的raceやloop数の多さを成果としない。

```sh
python3 -B experiment.py             # 保存原票の閲覧のみ
python3 -B checker.py                # read-only独立期待値・binding確認
python3 -B route.py locking
python3 -B route.py power-loss       # unsupported、exit2
python3 -B preview.py                # task-owned loopback、Ctrl-Cで終了
```

再観測だけは `python3 -B experiment.py --record` を明示し、最後に `python3 -B checker.py --record-binding`。通常checkerは原票や時刻を修復しない。実験は所有TemporaryDirectoryと6 writer process＋timeout用1processだけ。応答3秒、終了wait3秒、cleanup terminate/wait2秒後kill/wait2秒の上限を持つ。意図的timeoutはcommandを待つ所有processを0.15秒で検出しfinallyで回収。外部pathや任意command入力はない。

実務判断: 設定の+1やversion更新ではstableな別lockfileを全writerで共有し、**lock取得→最新read→計算→candidate完成→replace→unlock**を一つの保護区間にする。replaceするtargetinodeをlock対象にする設計はidentityが変わるため別検証が必要。advisory lockに参加しないwriterを防げず、process内threadやnetwork filesystemの規約も別。

atomic visibility、update isolation、durabilityは別判断。今回は指定順序で完全bytesのcheckpointと協力する2writerの直列化を実測。fsync、directory sync、電源断、NFS/SMB、Linux kernel、速度改善、全schedule、targetinode誤lock、multi-file transactionは未実証。lockしても電源断耐久性は増えたとは言えない。

今回coverage増分: lost updateの実反例、stable lockfileによる更新区間、commit前abortと競合解除、deadlock/停止の所有process回収。残る学習は次の3本:

1. **lock identity・非協力writer・optimistic version**: owned targetinode lockをreplaceして旧/new objectを分け、version checkの競合検出とretry上限を比較。[Apple flock](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/flock.2.html)
2. **durability protocol / recovery**: file sync→rename→directory syncの障害点を独立状態モデルで比べる。process crashと電源断を区別。[Apple fsync](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fsync.2.html)（次実験locator、今回本文未確認）
3. **multi-file / network filesystem**: 2file更新の片方commit失敗とreader整合性を比較。NFS/SMBは実対応環境の別scopeで規約確認。[Linux filesystem docs](https://docs.kernel.org/filesystems/index.html)（locatorのみ）

[原典](SOURCES.md) · [worker](worker.py) · [controller](experiment.py) · [独立期待値](oracle.json) · [UTC/環境/PID/raw](evidence/raw.json) · [binding](evidence/binding.json) · [実IAB QA](evidence/ui-qa.json) · [検証](evidence/verification.json) · [限定skill](skills/atlas-storage-locking/SKILL.md)

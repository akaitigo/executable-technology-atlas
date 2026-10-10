# ループ不変条件と停止

自然数 n の移送ループを、正常系 y+=1 と誤実装 y+=2 で比較する。先に予測し、本体を1回ずつ進め、途中状態と境界を分けて読み、原典と実装へ戻る教材。

この候補は新規単独unitの有限検証。global audit/gate、統合受理、commit/pushはこの担当範囲で実施していない。repository全体のcompleteは主張しない。

## 再現

このディレクトリで Python標準ライブラリのみを使う。通常実行はファイルを変更しない。

    python3 -B checker.py
    python3 -B runner.py
    python3 -B route.py
    python3 -B qa/check-ui.py
    python3 -B server.py

serverが表示する自分のportで http://127.0.0.1:PORT/ を開く。serverは自身のloopbackにだけbindする。他のportやtabを使わない。終了後Ctrl-Cで自分のserverを止める。receiptは最大512件のRAMのみ、保存する場合は停止前に /api/receipts を取得する。

観測保存は明示操作：

    python3 -B runner.py --record

新しいUTCディレクトリに子プロセスの入力、stdout、stderr、exit code、source SHA、時刻と凍結コピーを保存する。既存観測を上書きしない。

## 数学と観測を分ける

正常系の初期化 n+0=n。本体開始時 I∧x>0 より x≥1。x代入後は和 n−1、y代入後に和 n が復元する。出口 I∧¬(x>0) と自然数 x より x=0、したがって y=n。誤実装は和 n+1 となり保存に失敗する。

停止は別に、自然数variant xが本体ごとに1ずつ厳密下降することから紙上で導く。両方の本体は停止する。停止だけでは正しい答えにならない。Hoare部分正当性は終了した場合の事後条件を述べ、停止を証明しない。

公式 [Software Foundations Hoare](https://softwarefoundations.cis.upenn.edu/plf-current/Hoare.html) の While Loops本文（hoare_while）と、always_loop_hoare後のpartial correctness説明を2026-10-06に実読。途中で不変条件が一時的に偽になる説明を採用した。Rocq/Coqのインストールや機械証明は行っていない。

checkerのoracleは閉式、実装は反復代入。文字通りの手表5列、全162入力、固定12ケース、拒否追加6件、出力mutant12件を比較する。mutantは実装書換えによるmutation testingではなく、誤った出力フィールドを比較が拒否する確認。

早期QAで旧oracle-contract.mdの総数と途中添字の混用が見つかった。[訂正版v2](oracle-contract-v2.md)を現行契約とする。旧ファイルと初回観測は保持した。総数Kと本体番号jを分け、途中はx=n−j,y=s(j−1)、末尾はx=n−j,y=sj。実装と手表の値は変更せず再照合する。

UIは入力／予測変更時に古い結果を消す。stepはbudgetを増やして初期状態から再実行。toggleは同じn,budgetで正常／誤本体を変更して再実行。結果とSVGは実際の子プロセスstdoutから作成する。

実UIで固定60予測比較、編集8、step／切替6、stale消去4、reset12、実装等9viewerと公式本文1を確認し、最終80件の実行receiptとdesktop/mobile 3 JPEGを保存する。floatの3.0を3に正規化しないため、固定ケースはPythonで文字列化したstdinをそのまま渡す。失敗世代と修復理由はqa/README.mdに残す。

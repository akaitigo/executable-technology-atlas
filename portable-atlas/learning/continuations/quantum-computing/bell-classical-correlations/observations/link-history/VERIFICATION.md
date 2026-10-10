# 検証範囲

`python3 verify.py --record`は6ケース×Z/X、mixture重み5境界×2基底、CNOT全8列、15不正入力を実行する。独立した手書き有理数行列、部分トレースの明示的ブロック和、全15主小行列式の非負性、trace・Hermitian・Trρ²・coherence・確率・周辺確率を照合する。producerのtensor/gate/partial関数を期待値生成に使わない。

記録のUTC・環境・入力・source/artifact hashはobservations/raw.jsonとreceipt.jsonに保持する。通常checkerは読取りのみ、--recordだけ初回記録、--seal-recordは観測済rawを保持してreceiptを更新する。read-only proofは自己参照を避けreceipt対象外。

この有限単元の検証でありSubject全体・Core・Portal・repository full gateは未実行。独立AgentEvalではなく作者routing smokeである。

実IAB: 全12組の表示確率・判定をui-matrix.jsonへ転記しrawと照合。7回の実スクリーンショットを取得したがファイル未保存。先頭/末尾/前手順の操作境界、trace拒否、再正規化の意味不一致、原典・coverage展開を確認。専用tab11とsession54108/port55678を終了、残存listener0。保護対象PID3901/port53478は終了後もLISTEN、変更なし。default bindのEPERMはdefault-bind.txtに保存し、既存serve.pyの一回の承認実行で検証した。Skill quick_validate成功。

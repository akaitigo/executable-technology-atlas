# Atlas：既存の時計教材から増やす範囲

目標19はイベント到達関係と業務不変条件の独立照合を求める。元 `learning/subjects/distributed-systems/LEARNING_PATH.md:62` の実験1に対応する。原本の場所とhashは [sources.json](sources.json) に記録する。単体HTTP配信の外にある元ファイルを、画面から開けるリンクとして扱わない。[前提の案内](PREREQUISITES.md)から保存場所と読む箇所へ戻る。

| 既存にあること | 今回の扱い |
|---|---|
| 分散入口のLamport型counter、版の全順序、配送6順のmax比較 | 前提。計数や収束の新作にしない |
| Edge入口の2成分version vector、支配・競合保持、40配送例 | 前提。vector算法やhead比較の再制作なし |
| complete register historyのlinearizability、予約の収束と上限 | 既受入。別の問いとして案内のみ |
| 時計順≠因果順、表示step≠因果辺という説明 | 既にある説明を再利用 |
| 全15組の独立手表、合法再生順不変、逆推論2誤り・表示辺4誤り | 今回の有限検証の増分候補 |

独立手表と実計算の照合、実DOM・画像、限定Skillの利用、受入の状態は [status.json](status.json) で区別する。制作開始だけで教材数へ加算しない。作者加算0、元owner未確認・元repo未統合を維持する。

次の問いとして、ログ欠損や未観測通信、membership変更、vector pruning、causal consistencyの配送・読取り契約、実clock誤差、consensus・障害・耐久性が残る。今回の固定6イベントをこれらの保証へ広げない。

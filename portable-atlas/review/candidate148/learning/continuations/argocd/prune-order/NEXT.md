# 次課題の設計メモ：PruneLastの境界

これは未制作の次単元の設計です。現在のprune順序readerの独立受入後、別の専用ディレクトリ `argocd-prune-last-boundary` へ進める予定です。本メモを教材の検証完了や受入の根拠には使いません。

分野ゴール62のprune判断に沿い、今回読取済みの固定commit `sync_context.go` 1042–1058行を起点にします。本文は [source-review.json](source-review.json) に記録した同じ正式取得で確認した範囲です。全controller経路とHealthの保証を、このwave上書きの処理だけから導きません。

候補は次の4つです。期待値は次単元の模型実装前に独立した手計算oracleとして固定する必要があります。

|候補|比べる条件|確かめる境界|
|---|---|---|
|通常の逆wave|Sync apply wave 0/5、prune元wave −3/8|まずpruneだけの対称交換で初期の有効waveを作る。|
|全体PruneLast|同じ入力に全体指定を加える|Sync側の最大有効waveに1を加えた値へ対象pruneをまとめる。最大値にpruneも含まれる処理を確認する。|
|資源単位PruneLast|同じ入力でprune資源の片方だけ指定|指定していないpruneは通常の逆waveを保持する対照。複数資源の実際の完了順は扱わない。|
|全waveが負|Sync側の全有効waveが負の小例|最大値探索の初期値0を無視して、負の最大値+1にしない。|

追加する場合は、PreSyncの大きいwaveをSync最大値探索から外す例でphase条件を確認します。ただし、本処理はwaveOverrideを設定するのであり、phaseを書き換える処理ではありません。固定版の生成タスクとphaseの前提を読み直してから、ケースへ採用するか決めます。

LIVE Argo CD/Kubernetes、Healthの全状態、実時間、hookやretry、Prune=confirm/false、propagation/finalizerは別の境界です。未取得の分岐を推測で埋めず、今回の逆wave単元の原票やoracleも編集しません。

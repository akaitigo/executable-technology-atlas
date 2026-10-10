# 次の不足単元案：削除確認ゲート

分野ゴール62のprune判断に沿い、次の候補は `argocd-prune-confirm-gate` です。新しい専用pathで、現在waveの削除確認によって「prune段階へ進むか、手前でpendingを返すか」を比べます。まだ制作した単元ではありません。

起点は既読の固定版 [sync_context.go 1495–1502行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L1495)。現在のprune task集合と、確認が必要かの判定結果を準備済み入力とする4ケースを想定します。

|候補|予想する境界|
|---|---|
|確認が必要な資源なし|未確認でもゲートを通り、prune段階へ進む。実削除成功を意味しない。|
|現在waveに確認が必要な資源あり・未確認|prune処理へ進む前にpending。現在の組の処理を止める。|
|同じ現在wave・確認済み|確認ゲートは通る。権限やAPI成功を保証しない。|
|確認が必要なのは後続waveだけ|現在waveのゲート判定と、後続waveの判定を混同しない。|

`objRequiresPruneConfirmation` の文字列解析・default設定との関係、Prune=falseによる保護は本文全分岐をまだ確認していません。必要な固定版本文を正規に確認してから採用し、未取得部分を推測で断定しない方針です。この案だけで確認操作・実削除を実行するものではありません。

現在のPruneLast単元の独立受入後に、親の範囲調整に従って進めます。旧受入教材・原票・統合カウントは変更しません。

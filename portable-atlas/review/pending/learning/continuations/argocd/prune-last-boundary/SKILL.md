---
name: argocd-prune-last-plan-lesson
description: 通常逆waveとPruneLastの全体・資源単位指定を、固定5ケースの計画だけで対照するローカル教材。
---

# PruneLastの計画を手で追う

対象はこの独立単元のCLIと操作readerです。LIVEの同期や削除は行いません。前提は前単元の通常prune対称交換、Desired/Live、Sync phase/waveです。

画面で学ぶ場合は `index.html` をfile://で開く。候補waveと対象資源を予想し、通常逆wave→Sync最大値→指定後の順で3段階を読む。入力エラーをArgo実行失敗と混同しない。

1. READMEの基本4資源を見て、上書き先候補が6か9かを予想する。
2. `python3 -B model.py --case global --view input` で入力を見る。資源単位flagはlive側指定を判定済みとする仮定であり、annotation parserの検証ではないと説明する。
3. `--predict-wave 9 --predict-selected old-high,old-low` で対照する。通常逆wave後のpruneもSync最大値へ入ることを手計算表で確認する。
4. `resource-only`、`all-negative`、`presync-excluded` を順に読む。指定していないprune、最大値探索の初期値0、Syncだけの走査、phase保持を分けて説明する。
5. 固定commitの1042–1058行とsource-review.jsonへ戻る。同waveの資源名の並びを実行完了順と混同しない。計画へ配置されたことからHealthや削除完了を保証しない。
6. 必要なら `python3 -B verify.py` で軽い模型検査を行う。原票や実装前の手計算を上書きしない。文書変更後のhashを旧実行原票へすり替えない。

GUI・画像QAの記録はGUI-QA.mdを参照する。再実行時は共有browser枠を確認し、既存Chromiumをsandbox有効・専用profileで起動して自資源をcleanupする。install・LIVE Argo/Kubernetes・Docker・新サービス・OS設定変更は行わない。旧教材、統合repo、共有受入台帳、他ownerのファイルも変更しない。この単元の後に未指示の新単元を制作しない。

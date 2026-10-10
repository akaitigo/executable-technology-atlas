---
name: argocd-prune-confirm-gate-lesson
description: 選択済みの現在waveで、削除確認ゲートがpassかpendingかを固定4ケースで学ぶローカルreader・CLI教材。
---

# 現在waveの確認ゲートを手で追う

この独立単元だけで使う。LIVE同期、確認flagの変更、実削除を行うSkillではない。

1. index.htmlを直接開き、現在wave 0と後続wave 1の入力を読む。old-aが確認不要、old-bが確認必要のとき、old-aだけ先に削除するかを予想する。
2. `python3 -B model.py --case needs-confirmation --view input` で入力を見る。確認判定helperの結果は仮定であり、annotation/defaultを解析した値ではないと説明する。
3. `--predict pending --predict-blocker old-b` で照合する。確認ゲートの走査と、後ろのpruneループを区別する。
4. no-confirmation-needed、already-confirmed、later-wave-onlyの順に対照する。ゲートを通ることを削除成功やAPI権限の証明としない。
5. 固定版1495–1502行とsource-review.jsonへ戻る。未読helperやPrune=falseの挙動を推測で埋めない。
6. 必要なら `python3 -B verify.py` で軽い局所検査を行う。固定oracleと旧実行原票を上書きしない。文書hashは別metadataで管理する。

GUIは予想→3段階対照→原典→答えの順に操作する。予想変更・resetで古い結果が消えることは実操作確認済み。保存画像と実DOMの範囲はGUI-QA.mdを読む。独立受入は引継ぎ中。install、LIVE Argo/Kubernetes、Docker、サービス起動、OS設定変更、共有台帳加算、旧教材や他ownerpathの変更は行わない。

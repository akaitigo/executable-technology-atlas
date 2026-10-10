# Atlas：FCから未割当間の伝播へ

変数は置き場所、domainは置ける色の集合、辺は両端を異色にする制約です。assignmentは選んだ値、domainは残る候補なので区別します。今回は入力でA=0を固定する場合だけAのdomainを[0]にします。

読む順は、集合とqueue → 部分割当と制約 → FCと枝戻り復元 → 本教材のAC-3です。前作の探索全体を繰り返す教材ではありません。前作のFCが新しい割当の隣を調べるのに対し、今回は候補が減った先の未割当変数間にも影響を伝えます。

既存教材の場所はworkspace内 `independent-learning/ai-csp-domain-restoration/README.md`、根拠は同じ教材の `COVERAGE.md:7` です。学習の起点となる目標06は `2026-10-06/task-8/atlas-97-field-goals-ja.md:104–113`。現物のpath/hashは[前提読取記録](records/prerequisite-read.json)へ。教材単体のHTTP配信では、この外部workspace位置への遷移を確認済みリンクとして扱いません。

この単体教材では[4条件](CONTRACT.md)→[予想と操作画面](index.html)→[手計算](HAND_TRACE.md)→[原典の対応](reference.html)→[Skill](SKILL.md)と辿れます。全16割当の手表と、FC/AC-3の記録を混ぜずに比較してください。

実務では、候補を消した根拠・再確認が必要なarc・停止理由を説明できることが先です。非空候補だけで「解がある」と決めず、探索や別の十分な確認が必要か判断します。計数の大小を、そのまま実時間の優劣に置き換えません。

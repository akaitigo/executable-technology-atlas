# 検証記録

問い：tool許可とplan決定権を分け、有限実行で停止・拒否を監査できるか。経路：Mac直接Python標準ライブラリ→著者plan/dummy store→状態機械→raw audit→一時HTTP→実IAB。

AI推論・LLM自律動作・外部toolは未実行。authoredはtoy fixtureの出所で実ユーザー/OS権限ではない。bad variantは固定structured proposalの昇格を意図的に行い、一般の攻撃検出器の性能を測らない。

18case×2policy、100個のseed固定直線planを2予算で比較、手動transition/status/steps/value/call/pc oracleと独立phase inductionを照合。通常checkerはread-only、原票更新は明示 --record。作者routing smokeは独立AgentEvalではない。

時刻・環境・input/tools/source/artifact digestはobservations/receipt.json。実IAB、capture保存可否、ownedserver/tab終了はobservations/ui-qa.jsonへ保存。Subject全体/実agent基盤/LLM/本番権限/安全保証は未完成。指定外path、Portal/Core、Goal、commit/pushは変更せず、全体gate/full verifyは今回未実行。

## 実行結果

`python3 verify.py --record` と通常 `python3 verify.py` はpassed。18case×2policy、100直線plan×2budget、top-level拒否6件、option拒否3件。手書き終端・値・step・tool回数・pcと独立遷移表に一致。seedは20261005。taintedはguard7 / bad104、badだけtool-data呼出し。

初回はjumpのdetail keyがtransitionのtarget引数と衝突しTypeErrorになった。`jump_target`へ修正して再実行、初回失敗を[iteration-failure](observations/iteration-failure.txt)へ保持。



最終UIで[36終端観測](observations/ui-matrix.json)とrawを比較。正常OBSERVE値4、bad promotionのtool-data/pc0とadd(4,100)/authorized_plan=false、guardのproposal_ignored=true/pc1を観測。slider・前後・終端ボタン、入力拒否/receipt disclosure、9領域・次の4実験を確認。summaryはPlaywright button roleでno_matchesになったため、実UIのvisible textで開き直し成功した。グラフ矢印がnodeへ隠れる初期表示を修正し、矢印方向と選択edge/nodeを実captureで確認した。

実captureは5枚取得、CUA tool出力に表示したがファイル保存はしていない。captureのhashや代替描画は主張しない。owned tab5はclose、owned server session36644はCtrl-C→exit0/finally server_close。

module Skillはquick_validate passed、budget対応 / llm-agent未対応の作者smoke passed。独立AgentEvalではない。最終通常checkerの全moduleファイルhash前後一致は[read-only proof](observations/read-only-proof.json)。証拠ファイルを書く操作はcheckerと別に行った。

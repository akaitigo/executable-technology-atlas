# 検証記録

問い：実stdlib spawn worker2個の整数sumについて、分割/正常/意図bug/worker error/timeoutを独立閉形式とcoverageで検査できるか。Python stdlib→owned2worker→rawtimeline→一時HTTP→実IABで確認する。8case×2policyの16実run、100seed固定partitionvector×2policy、invalid8、integer/float結合則反例。非決定PID/elapsed/UTCは実観測として保存し、再検査はsemantic結果とcleanupを比較。

通常checkerはfile read-only。原票更新は明示--record、QA後のreceipt固定は--seal-recordで観測rawを維持。作者Skill smokeは独立AgentEvalではない。全repository gate/full verify、MPI/SIMD/GPU/cluster、性能優位/scalingは未実行。今回の専用module外/Portal/Core/Goal/commit/pushは変更しない。

実IAB全8×2=16選択のvisible summaryを照合。正常/端数bug図、worker-error None、timeoutのterminate_owned理由・exit-15/alivefalse、event前後/端点、結合則回答、原典7件/10領域/次4実験を確認。実capture7枚はinline取得・目視、ファイル保存なし。owned tab9 close、dynamic127.0.0.1:62849 server session83052 Ctrl-C exit0。default bind EPERM・favicon404/データGET200/304を保持。Skill quick_validate/正常と未対応作者routing smoke成功、独立AgentEvalなし。

初回invalid reversed試験のstart9/stop9は空区間だったためstart10へ修正、失敗記録を保持して再実行成功。通常checkerの全module bytes不変証明はobservations/read-only-proof.json。QA後は--seal-recordで観測rawを変更せずreceiptを固定する。

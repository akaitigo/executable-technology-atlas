# 検証記録

問い：計算した複素basebandとphase/noise/pilot境界を独立成分算術とbitvectorで検証できるか。Mac直接Python stdlib→実complex計算I/Q array→raw→一時HTTP→実IAB。実電波/SDRdevice/GNU Radio/規格適合は未実行。

11case×2policy、100seed固定vector×2policy、samples/symbolの保持平均比較、invalid18件/nonfinite4件/option3件。Fraction成分oracleと手書きdecoded/error vector、sample/平均/factor/BERを照合。payload16bits/64complex samples、pilot4bits/16samples。通常checkerはread-only、原票更新は明示 --record。作者Skill smokeは独立AgentEvalではない。

時刻・環境・input/source/artifact hashはobservations/receipt.json。実IAB/capture保存可否/ownedresource終了はobservations/ui-qa.json。統計AWGN BER、実timing/RF性能、規格/安全保証は未実行。指定path外/Portal/Core/Goal/commit/pushは変更しない。全体gate/full verifyは今回未実行、全Subject完成とはしない。

実IABは11×2=22選択のvisible summaryを照合済み。symbol前後/端点、計算sample波形、原典5件、10領域と次4実験を確認。実画面capture6枚はtool inlineで取得・目視、ファイル保存なし。スクリーンショットdigestを作っていない。dynamic127.0.0.1:61460のowned tab8をclose、server session38312をCtrl-C、exit0。default bind EPERM・favicon404も記録を保持。Skill quick_validate成功、supported bpsk/unsupported rf-transmit作者smoke成功（独立AgentEvalなし）。

最終通常checkerの全module file bytes前後比較はobservations/read-only-proof.json（証明recorderはchecker終了後に書く）。

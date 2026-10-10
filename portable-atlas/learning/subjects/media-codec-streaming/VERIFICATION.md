# 検証記録

問い：実WAVのformat/data/sampleを観測し、到着順とPTS順、待機とunderflowの差を有限模型で検証できるか。経路はMac直接Python stdlib→実WAV bytes/readback→固定arrival模型→raw信号/timeline→一時HTTP→実IAB。

mono16/8000Hz、320frames/40ms、684WAV bytesを実行。独立RIFF/sample oracle、36手動timeline、100random timeline×2policy、input/option拒否22件/WAV拒否4件、signed境界を検査。通常checkerはread-only、原票更新は明示 --record。作者Skill smokeは独立AgentEvalではない。

時刻・環境・input/source/artifact hashはobservations/receipt.json。実IAB/capture保存可否/ownedresource終了はobservations/ui-qa.json。H264等製品圧縮codec、実ネットワーク/配信、OSdeviceの再生timing、主観音質は未実行。指定path外/Portal/Core/Goal/commit/pushは変更しない。全体gate/full verifyは今回未実行、全Subject完成とはしない。

## 実行結果と実UI

`python3 verify.py --record` / 通常 `python3 verify.py` はpassed。320frames/684WAV bytesの実readback、独立manual RIFF/sample、36手書きtimeline、100random arrival×2policy、audio10/packet7/option5拒否、WAV4拒否。source WAVとreordered PTS delay30 WAVはbyte一致、arrival-order delay30とunderflow WAVは異なる。実WAVのSHA-256はraw/receiptに保存。

実IAB actual port59223/tab7でsource.wavをHTTP取得し、browser DataView header/sample＋SHA-256を表示。684bytes/320frames/40ms/format tag1/block align2/byte rate16000、header hexと先頭16sampleがPython/rawに一致。[36UI行](observations/ui-matrix.json)のstatus/underflow/並び違い/source一致/peak/提示seqも照合。

reordered PTS delay0のzero fill、delay30の正常信号、arrival-order delay30のseq1↔2交換、lossの待機後も欠落を実画面で確認。slot1deadline40msではguard seq1/residence15ms、bad seq2/residence18ms。前後/終端/slider/select、header/input/rejection/receipt disclosure、10領域/4次実験を確認した。信号のx軸をsample i/320へ調整し、slot提示seq/colorを追加して最終36行を再観測した。

capture5枚は実CUA出力取得、ファイル保存なし。最初のheader captureは信号ラベル調整前、残り4枚は最終UI。capture hash/代替描画は主張しない。[QA](observations/ui-qa.json)はraw/UI/sources/coverage/WAV bytesへ結合。実音の聴取やOS再生時刻の計測はしていない。



Skill quick_validate、wav対応/h264未対応smokeはpassed（作者smoke、独立AgentEvalではない）。最終read-only checkerの全既存moduleファイルhash前後一致はobservations/read-only-proof.json。記録writeはcheckerと分離。全体gate/full verify、製品圧縮codec/実配信ネットワーク/音質/実timingは未実行。

# 有限検証

2fixture×256pixel=512sample。各136covered/120背景、計272covered/240背景。正規化viewportのscreen重みと、独立camera ray-plane交点によるworld重み/UVを全sampleで照合する。同w全covered一致、異wでは辺上の一致も許して内側の差を確認する。基準sampleと3頂点の手書き境界も確認。15contract拒否はEXPECTED_REFUSALとして正常描画件数と分離する。

6PNGをCPUで実生成し、producerとは別のchunk/CRC/zlib/filter0 decoderで全1536pixelを検査。PNG hashだけの一致を画素照合と呼ばない。Fractionなので計算値は厳密有理数。PNG量子化は固定round-half-up。

observations/attempt-01/raw.jsonに入力・全sample・camera交点・UTC・command・環境・exitを保持し、receipt.jsonにsource/input/artifact hashを束縛する。checker/routeの内容hash+mtime不変は外側recorderが検査後に記録する。read-only proofは自己参照を避けreceipt対象外。

全体Core/Gate、Subject全体、実GPUは未実行。Skill routingは作者smokeであり独立AgentEvalではない。

実IABで2条件×基準点/4pixelの10組を観測し、5不正入力の拒否と選択維持を確認。異w pixel(3,3)はnaive RGB=(112,56,40)、correct=(71,36,220)、difference=(41,20,180)。実生成PNGの表示・ブラウザdecode、原典/coverage展開、producerとoracle source閲覧を確認。実capture5回、ファイル未保存。専用tab13、session8730/port59284を終了し残存listener0。保護対象PID3901/port53478はLISTEN維持。default bind EPERMは保存し、一時localhostの承認実行で確認。初回receiptはinitial-receipt.jsonとして保持し、新receiptはraw/PNGを変えず現在checker/QA日時を束縛。

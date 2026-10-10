# 検証記録

既存CPythonの実加算、math.fsum、ID欠落を7条件で計算。原票にUTC/runtime/入力/途中値/結果/ID/count/例外とsource hashを記録。初回receipt/rawを保存し、QA後のcurrent receiptを別seal。通常checkerは実再計算と独立oracle照合を行うがfileは書かない。全file hash/mtime前後一致をproofへ最後に保存。

実IABで各条件、予想全4選択、開いた答えから予想のみ変更、条件/inputreset、拒否位置の保持、成功後のexecutor失敗、保留した旧応答、原教材/数値計算/実装/手表/oracle/README6導線を確認。captureはtool画像。保存不能ならpath/hashをnullとして明記する。所有tab/serverのみ終了。他owner listenerの実前後PIDは原票に残す。

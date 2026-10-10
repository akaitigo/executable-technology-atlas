# 検証範囲

固定手表→独立literal oracle→実runnerの7条件29eventを照合。原票はUTC、runtime、health入力、event/generation/desired/actual/health/Synced/stage2開始数、意図例外とsource digestを持つ。初回raw/receiptは更新せず、current artifact/source bindingをsealする。

実IABはPython localhost APIを呼び、7条件、全位置、予想全4選択への単独変更（成功比較→答えを開く→予想だけ変更）、条件/inputreset、位置拒否の保持、成功後の実RuntimeError注入、保留旧応答の非採用、6本のsource導線を検証する。captureは実tool画像。保存不可ならsaved=false/path/hash=nullとして再構成しない。所有server/tabのみ終了、他owner listenerは操作しない。

通常checker/route/限定Skill検査は読み取り専用。全file sha256/mtimeを前後比較し、proofを最後に書く。理解度、実製品、全Subjectの完了を検証したとは主張しない。

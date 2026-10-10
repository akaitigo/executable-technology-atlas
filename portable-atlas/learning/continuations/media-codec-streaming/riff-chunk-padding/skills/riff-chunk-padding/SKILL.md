---
name: riff-chunk-padding
description: 保存RIFF chunk/padと実waveの観測を読み、照合し、明示指定時だけ新runを記録する。
---

このmodule内の既存worker/runner/checker/UIへrouteする。
python3 route.py inspect はread-only、lessonはUI位置。
利用者が新規記録を明示した場合だけ python3 route.py record。旧rawを保つ。
未知routeはexit2。元Subject/他continuation/Portal/利用serverを変更・停止しない。
strict教材契約とwave実挙動を別に扱う。bounded fixture/input/readframesのみ。
実IABで条件と予測変更後の結果/答えreset、入力拒否の対照表示を確認する。
RF64/圧縮codec/再生品質/配信/汎用format保証を主張しない。

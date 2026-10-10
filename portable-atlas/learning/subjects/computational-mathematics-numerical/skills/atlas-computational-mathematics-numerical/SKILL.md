---
name: atlas-computational-mathematics-numerical
description: 浮動小数点の小規模総和をPython stdlibで比較し、naive・Kahan・Neumaier・Fraction oracleの実測と操作画面から丸めを説明する。この教材の総和実験を再利用するときに使う。
---

# 浮動小数点総和教材の再利用

教材rootはこのSkill directoryから`../..`。まず[README](../../README.md)の入力範囲と実測表を読む。理解確認は「予想→入力/順序操作→正常と境界の比較→一次資料/実装→答え」で進める。

- 既存結果の検査: 教材rootで`/usr/bin/python3 -B verify.py`。実測原票は[python.json](../../observations/python.json)と[stdout.txt](../../observations/stdout.txt)。現在source digestに合わなければ古い観測と明示する。
- 新しい小規模総和: [lesson.py](../../lesson.py)の`experiment(tokens, order)`を使う。tokensは十進数文字列1〜32個、orderは`original`/`reverse`/`small-first`。入力変換後floatの正確な総和と、十進数文字列の正確な総和を区別して誤差を説明する。
- 図と数値step: 教材rootで`/usr/bin/python3 -B lesson.py --port 18746`を起動し、[UI](../../index.html)をloopbackで操作する。既存実画面は[media](../../media/)、HTTP原票は[http.json](../../observations/http.json)。新たな観測保存は明示依頼時に`lesson.py --record`を使い、保存済み結果を更新する効果を説明する。

`[1e16,1,-1e16]`は基本Kahanも0となる境界例。Neumaierやsortが任意入力で厳密になるとは主張しない。Pythonの値を画面表示する実装なのでJavaScriptとの精度差は未測定と返す。

行列/ODE/FFT/条件数/並列reduction/GPU/高精度数学全般の依頼はこの教材では未対応と伝え、既存実験で証明した範囲を示す。理解度や分野全体の完成はこの観測から判定しない。教材専用directory外への変更やglobal Skill installはこの入口の用途に含めない。

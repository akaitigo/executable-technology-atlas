---
name: atlas-mathematical-statistical-foundations
description: 既知の合成有限populationの2x2表から条件付き確率・Bayes・base-rateをFractionで比較し、条件の逆転と分母ゼロを操作教材で説明する。この有限集合教材を再利用するときに使う。
---

# 条件付き確率教材の再利用

教材rootはこのdirectoryから`../..`。[README](../../README.md)の入力表・scopeを確認し、予想→counts/条件操作→正常と境界比較→一次資料/実装→答えの順に進める。

- 保存済み結果の読み取り検査: 教材rootで`/usr/bin/python3 -B verify.py`。通常実行は原票を書き換えない。原票は[python.json](../../observations/python.json)、[stdout.txt](../../observations/stdout.txt)、[HTTP応答](../../observations/http.json)。source bindingが古い場合は古い観測と明示する。
- 小さな新入力: [lesson.py](../../lesson.py)の`calculate({'ap':整数,'an':整数,'bp':整数,'bn':整数})`を使う。cellはA+/A−/B+/B−、合計1〜2000の既知population。`probabilities`、`enumeration_oracle`、`bayes`を照合する。
- 図で分母を確認: 教材rootで`/usr/bin/python3 -B lesson.py --port 18747`を起動し、[UI](../../index.html)で全体/A/test+集合を切り替える。[実画面](../../media/)と[DOM原票](../../observations/ui-dom.json)も参照できる。起動した専用serverは利用終了後に停止する。

感度`P(test+ | A)`とPPV`P(A | test+)`は条件が逆。分子が同じでも分母を明示する。分母0は`fraction: null`で未定義を返し、0へ置き換えない。空classを条件とする確率と、そのclassのjoint mass 0を区別する。百分率は表示用近似、Fractionが正本。

実populationの推定、推測統計、連続分布、医療個別判断、線形代数、最適化はこの教材では未対応と返す。合成populationの計算から現実の率や利用者の理解度を認定しない。既存観測の更新は明示依頼時の`lesson.py --record`/checkerの`--record-*`で行う。この入口はglobal install、別repository編集、公開へ用途を広げない。

# PIの飽和・windupと有限観測の回復

[既存学習経路](../../../subjects/control-systems-simulation/LEARNING_PATH.md) §6実験2を独立pathで実行する数学CPU教材です。[有限契約](CONTRACT.md)と[初期手計算・境界手表](hand-oracle.json)を先に固定し、旧y/zから要求uと次y/zを求めます。plantの保持入力区間厳密更新を採り、controllerの離散積分とsolver誤差を混ぜません。既存実験1・旧教材・global入口は変更していません。

予想→h/方式/Kiを操作→飽和なし/積分継続/条件付き停止とP対照→原典・実装・原票→答えの順です。条件や予想変更は旧結果を消去。h=.25/.5、3方式、Ki=0/1の有限12条件です。

## 再現

Python 3.9以上の標準ライブラリのみ、install不要。このディレクトリで `python3 -B serve.py`、表示された127.0.0.1 URLを開きます。別terminalで `python3 -B verify.py` または `python3 -B route.py`。serverはCtrl-Cで終了。sandboxがloopbackを拒否した時は失敗を残し、通常host許可reviewで同じ専用資源を検査します。

初回作成者用 `verify.py --record attempt-01` は既存原票の上書きを拒否。UI後の `--seal-record` は初回receiptを保存し現在source/観測を束縛します。通常verifyは再実行・照合のみで書きません。

## 実観測の代表

τ=1、Kp=1、上下限±1、4秒までr=4、その後r=.5、8秒まで観測。PIの積分継続はh=.5でz(4)=13.24747、h=.25で13.10950、目標を下げても8秒まで上限clipが続きます。条件付き停止はz(4)=0で、切替後の実入力が上限から外れます。Ki=0ではzを保存しても積分寄与が0なので、飽和/条件付き停止のy/uが一致します。

全12条件が今回の定義では窓内未整定です。h=.5/conditional/PIは8秒で初めて±.05帯内に入りますが、残り1秒がないため整定済みとしません。h=.25/conditional/PIは4.5秒に初回到達し4.75秒に再逸脱、8秒時点y=.44533で帯外です。初回到達・再逸脱・整定は別の指標です。窓を延長した結果、sample間の挙動、一般的な回復時間を実証したものではありません。

h変更はsampled controllerと判定点の差です。plantは各保持入力区間を指数関数で更新し、Euler truncationを採っていません。浮動小数点丸めは独立Decimal70漸化式と相対/絶対許容1e-10で照合。高精度でも実plantとの差は埋まりません。時系列図の線はsampleの視覚補間、sample最大超過も連続時間最大値ではありません。

## 原典・検証・限界

MIT 6.302 Recitation 6本文の積分/定常偏差は概念入口です。[sources](sources.json)で範囲を分けます。anti-windupの等値・外向き停止、sampled model、reference列・判定規則は独自です。実plant設定、HIL、安定性、安全性の保証ではありません。[COVERAGE](COVERAGE.md)に未対応を残します。

[controller](controller.py) → [独立Decimal oracle](decimal_oracle.py) → [検査器](oracle.py) → [整定判定](metrics.py) → [全原票](observations/attempt-01.json) → [検証範囲](VERIFICATION.md)。実画面captureはtool表示で確認し、保存pathが得られない場合はsaved=falseと記録します。分野全体・Core完了、commit/push/公開は今回の主張に含めません。

# 観測遅延と1D制動距離を面積から確かめる

[既存point-grid教材](../../../subjects/robotics-autonomous-systems/README.md)の次実験3を独立pathで制作した有限数学simulationです。旧gridの瞬時STOP、footprint実験、原票、global入口を変更していません。[有限契約](CONTRACT.md)と[単位付き手表](hand-oracle.json)を先に固定し、遅延中の長方形面積と制動中の三角形面積を実Pythonのpiecewise時系列へ照合します。

予想→fixture/仮定/表示h→遅延あり/遅延0/瞬時停止対照→実装・独立oracle・原票→答えの順で進めます。10fixture×3仮定×h=.5/1の60条件。hは表示sampleの間隔、停止判断や物理モデルの周期ではありません。

## 再現

Python3.9以上の標準ライブラリのみ、install不要。このディレクトリで `python3 -B serve.py` を実行し、表示された127.0.0.1 URLを開く。別terminalで `python3 -B verify.py` または `python3 -B route.py`。serverはCtrl-Cで終了します。sandboxのloopback拒否は失敗として残し、通常host許可reviewで同じ専用資源を確認します。

初回作成者用 `verify.py --record attempt-01` は既存原票を上書きしません。UI後の `--seal-record` は初回receiptを保存しsource/観測を束縛します。通常verifyは再実行・照合だけで書きません。

## 有限観測を読む

v=2m/s、a=2m/s²では遅延0の停止距離1m、遅延.5秒で2m、遅延1秒で3m。同じ障害2mに対し.5秒遅延は停止位置で接触、1秒遅延は停止前に接触。等値をclearにしません。瞬時停止仮定は時刻0で速度jump、位置0という別modelで、有限制動や旧gridの同一fixtureではありません。

between-samplesの接触時刻は.5+(2-sqrt3)/2≈.6339745962秒。h=.5では.5/1秒、h=1では0/1秒の間で起きる解析eventです。sampleが障害点と一致する時だけ接触とする方法では見落とします。表示hを変えても解析距離・event時刻は変わりません。

delay-windowはT=1秒で位置4m/速度4m/s、停止距離12m・停止時刻5秒は解析的に既知でも窓内未停止。障害6mの未来到達は約1.535898秒で窓外です。braking-windowはT=1で位置3.5m/速度3m/s、停止距離8m/時刻4秒、障害10mへの接触はモデル内で存在しません。zero-horizonはT=0の初期点だけ。v=0は遅延値に関係なく時刻0から停止、L=0は初期接触です。

## 原典・証拠と限界

[LaValle原典確認](sources.json)の位置/速度state・動力学は概念入口。遅延中一定v、その後一定a、静止点障害物の距離式と接触規則は独自導出です。原典所定の安全gateとは呼びません。[COVERAGE](COVERAGE.md)の未対応を今回の成功で埋めません。

[実装](motion.py) → [独立Decimal70面積oracle](area_oracle.py) → [検査器](oracle.py) → [全原票](observations/attempt-01.json) → [検証範囲](VERIFICATION.md)。位置は旧stateの数値積分ではなく解析関数。速度面積と別形の到達式へ照合します。図の線はsample点の視覚補間、接触後の軌跡は衝突応答を含まない反実仮想です。

実画面captureはtool表示で確認し、保存pathがない場合はsaved=falseと記録します。実robotの設定値や安全距離の助言、実sensor・摩擦・制動hardware・安全保証は含みません。分野全体/Core完了、commit/push/公開も今回の主張に含めません。

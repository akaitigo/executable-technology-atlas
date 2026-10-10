# 有限契約・単位・手表

理想1D点モデル、初期位置0m、初速v>=0 m/s、観測/反応遅延tau>=0秒。遅延中v一定、その後減速度a>0 m/s²でv=0まで減速、以後位置を保持し逆走しません。摩擦/sensor/hardwareはありません。障害は固定位置L>=0mの点。経路x(t)は接触後も反実仮想として計算し、衝突応答はモデル化しません。

遅延ありは指定tau、遅延0は同じv/a/Lでtau=0。瞬時停止はt=0の右側でv=0、位置0、停止時刻0という別仮定。初速パラメータはその瞬時jumpの前の速度です。有限aでこのjumpを実現したとは扱いません。旧gridの瞬時STOPを同一実験として追試したものではありません。

v>0では停止時刻tau+v/a、停止距離v*tau+v²/(2a)。v=0はtauに関係なく時刻0/位置0で停止済み。遅延長方形面積v*tau、制動三角形面積(v/2)*(v/a)を独立に照合します。

| fixture | v / tau / a | L / 終端T | 距離 遅延/遅延0/瞬時 (m) | 遅延停止時刻 (s) |
|---|---|---|---|---|
| rest-clear |0/1/2|1/2|0/0/0|0|
| rest-contact |0/1/2|0/2|0/0/0|0|
| zero-delay-clear |2/0/2|2/3|1/1/0|1|
| delay-touch |2/.5/2|2/3|2/1/0|1.5|
| delay-contact |2/1/2|2/3|3/1/0|2|
| between-samples |2/.5/2|1.25/3|2/1/0|1.5|
| delay-window |4/1/1|6/1|12/8/0|5|
| braking-window |4/0/1|10/1|8/8/0|4|
| zero-delay-contact |4/0/2|3/3|4/4/0|2|
| zero-horizon |2/.5/2|1/0|2/1/0|1.5|

障害L=0はINITIAL_CONTACT。0<L<停止距離はCONTACT_BEFORE_STOP、L=停止距離>0はTOUCH_AT_STOP、L>停止距離はNO_CONTACT_IN_MODEL。接触等値をclearと呼びません。解析到達時刻を先に求め、T以内はEVENT_IN_WINDOW、Tより後はFUTURE_EVENT_OUTSIDE_WINDOW。接触が存在しない時刻はnull。サンプル点だけを接触判定に使いません。

表示刻みh=.5/1秒。0からTまでの表示sample、T端点を保存し、遅延終了・停止・接触の解析eventをsampleと別保存します。between-samplesの接触は.5+(2-sqrt3)/2≈.6339745962秒で.5/1秒の間。eventの左/右sample時刻とsample一致の有無を記録します。数式を評価するため、hは物理モデル/solverの刻みではなく表示点の間隔です。

終端状態はT>=停止時刻ならSTOPPED_BY_HORIZON、それ以外はNOT_STOPPED_BY_HORIZON。停止距離・停止時刻は解析的に既知でも窓内停止の観測とは別です。T=0は初期点1つだけ。遅延終了と制動開始の等値はBRAKING、停止時刻等値はSTOPPEDを優先します。有限10fixture×3仮定×h2値の60条件です。

負v/tau/L/T、a<=0、bool/文字列/nonfiniteを物理入力として拒否し、h<=0も拒否します。公開UI/APIはfixture/mode/hの有限選択のみ。これは実robotの安全距離の助言ではありません。

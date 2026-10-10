# rankとridgeの目的関数を分ける

前提は2列の行列、線形結合、二乗和、切片なし回帰。[元教材のOLSと評価範囲](../../../subjects/data-science-statistical-learning/README.md) → このUIで予想・条件操作 → [実装前に固定した手表](hand-oracle.json) → [独立閉形式](oracle.py) → [公式原典locator](sources.json) → 答えと実務判断の順。[正確な値とfloat丸め](../../../subjects/computational-mathematics-numerical/README.md) はFraction一致からfloatの安定性を推論しないための関連教材。

## 入力と目的を固定する

独立X=[[1,0],[0,1]]、y=[2,3]はrank2。相関X=[[1,1],[2,2]]、y=[2,4]はrank1。目的J=Σ(Xw−y)²+λ(w1²+w2²)。RSSは平均にしない。整数入力2..4行、2列、X値−5..5、y値−20..20、非零行列、整数λ0..4。boolを整数と扱わない。

実装より先に手表を保存した。独立OLSは(2,3)、RSS0。独立ridge λ1は(1,3/2)、RSS13/4、罰則13/4、合計13/2。相関OLSはw1+w2=2でRSS0、係数は非一意。代表(2,0)のnorm4はOLSの罰則ではない。相関ridge λ1は(10/11,10/11)、RSS20/121、罰則200/121、合計20/11。rank(X)は1のまま、正則化した係数行列はrank2となる。

producerはFractionでGramと右辺を作り、消去法でpivot・自由変数・null方向を求める。singular OLSを非一意として返し、失敗へ置き換えない。oracleはsolverをimportせず、固定Gram/係数と別の閉形式で照合し、各成分の正常方程式と目的関数を検査する。非一意の5候補、4条件×49候補の目的差の平方展開を確認する。平方展開はこの固定行列に限る。7画面条件には負λ・形状拒否と意図的なFractionゼロ除算によるEXECUTION_FAILUREも含める。

## 再現と証拠

```sh
python3 -B verify.py
python3 -B route.py
python3 -B serve.py
```

stdlibだけ。scikit-learnは実行しない。UIは保存された実Python観測を表示し再学習しない。通常checker/routeは書かず、全ファイルhash/mtimeを前後確認する。原票は明示未使用 `--record attempt-01` だけで作る。rawの入力・手表・source hash、UTC、Python環境、command、exitとUI観測を区別する。負λ・形状・boolなど17拒否、6結果改変も検証する。

## 原典と実用判断

[scikit-learn公式OLS §1.1.1](https://scikit-learn.org/stable/modules/linear_model.html#ordinary-least-squares) は残差平方和を最小化する目的を説明する。[Ridge §1.1.2.1](https://scikit-learn.org/stable/modules/linear_model.html#ridge-regression-and-classification) は係数ノルムの罰則を加える別目的を示す。本教材は切片なし・正確な有理数・固定λで、ライブラリのsolverを再現したものではない。

係数が一意か、予測が同じか、目的が何かを分けて判断する。相関OLSの係数だけに一つの解釈を押し付けない。ridgeでRSSが増えても罰則込みの目的と比較する。λ=1の選択理由は学習用固定条件で、実データでの推奨ではない。現実性能、float安定性、λ選択、評価分割は未実証。Subject/Atlas全体の完成ではない。

次は近い相関列でfloatと正確計算を比較、尺度変更による罰則の意味、validationでのλ選択を個別に検証する。

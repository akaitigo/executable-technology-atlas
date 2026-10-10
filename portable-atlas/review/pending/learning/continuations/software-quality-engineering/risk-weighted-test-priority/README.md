# impact重みとテスト優先順位

既存QE教材のCOVERAGE③から切り出した、有限な選択と実行の教材です。架空のfailure mode A/B/Cに重み8/7/6を与え、4テストの宣言coverageの和集合を評価します。重みは恣意的なimpact unitsで、事故確率・金額・製品品質ではありません。costも抽象unitsで、実行時間ではありません。critical Aは架空の必須条件です。

|test|cost|対象mode|
|---|---:|---|
|T1|3|A,B|
|T2|2|A,C|
|T3|2|B|
|T4|1|C|

budget=3では追加重み/costによるgreedyがT2（14）、全16subset列挙の最適がT1（15）です。同点の全列挙はcost最小、sorted ID辞書順。budget=4ではT1,T4を選びます。greedyは正の追加gainだけをexact Fractionで比較し、同点はID順、選択後にcriticalを検査します。critical必須のbudget=0/1は全列挙によってINFEASIBLE。greedyだけの失敗から不可能とは推論しません。

境界の仕様は`x in set(range(lo,hi))`。A=[2,5,2]→true、B=[2,5,5]→false、C=[2,2,2]→falseを実Python関数へ渡します。normalは`lo<=x<hi`、lowerは下端除外、upperは**非空区間だけ**上端包含、emptyは空区間の点を受理する故障です。以前の別教材の上端故障とは条件を混同しません。

選択して制約を満たす計画だけを実行します。NOT_RUNは未実施、NO_DIFFERENCE_DETECTEDは実施して集合仕様との差なし、DETECTEDは差を検出した状態。宣言coverageは検出成功とは別です。budget=3のupperではgreedyがBを実施せず、optimalのT1はBの故障を検出します。正常版の差なしも品質全体の証明にはなりません。

`python3 -B verify.py`と`python3 -B route.py`は保存原票と独立手表を読み、48条件・17拒否・8mutantを確認します。記録生成とsealは制作時に一度だけ実施済みで、通常の再現では上書きしません。`python3 -B serve.py`は127.0.0.1の動的portを表示します。表示されたindex.htmlを開き、予想→条件→実行→比較→source→答えを操作します。停止は自身が起動したサーバーのCtrl-Cだけ。追加パッケージや外部サービスは不要です。

source viewerは文字数を明記し、32768文字を超える原票は冒頭抜粋と完全ファイルへのリンクを示します。保存JSON自体は完全です。2つの既存教材参照は読み取り専用で、本教材の実行には不要です。ブラウザ証拠は実ツール観測の圧縮転記であり、CLI原票をブラウザから取得した全文とは呼びません。ツール内スクリーンショットは保存画像ではありません。

原典は[sources.json](sources.json)のISTQB CTFL v4.0.1 §5.1.5／§5.2.3。原典のrisk分析はlikelihood・impactや関係者の判断を扱います。このimpact-only subset模型と固有の数値・算法は独自の教学例です。全科目、Core、実運用品質の完成は主張しません。

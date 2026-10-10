# 観測範囲と限界

|経路|実測対象|制限|
|---|---|---|
|事前手表|10fixture、small root=0、残差尺度、zero/近重根|一般の誤差上限ではない|
|独立oracle|Fractionの元/丸めた係数、Decimal sqrt160/240桁の90桁一致|有限桁差32桁を事前に見込んだfixtureだけ|
|誤差|全40根の総/演算forward errorと変換差|zero基準の相対値null。誤差表示35有効桁|
|residual|全40根×元/float係数の2多項式をFractionで厳密評価し、別Horner式でも照合|正式なbackward errorや全solver適合性ではない|
|拒否|bool/文字列/nonfinite/a0/負判別式/中間範囲/q0/根overflowなど13件|拒否条件を含む有限実行|
|故障変種|q符号/abs(b)/分母/積式/zero特例/zero根の6変種|実変種のwitness。通常公式自体とは区別|
|IAB|20条件、2方式比較、予測、変更、reset、実source link|CUA実操作＋DOM。成功CLIを実表示に代えない|
|HTTP|20正常応答と13不正JSON等の拒否|自分の動的localhostのみ|
|メディア|実表示のtool capture|inlineのみ。保存画像・path/hashを捏造しない|
|封印|hash receipt、read-only hash/mtime proof|module有限検証のみ、global gate未実行|

browser projectionは独立literal期待値と比較してから、同じCLI値を手動転記templateとして使う。rootは同じbinary floatへの数値一致、stringの高精度誤差・Fraction residualはexactに照合する。各観測とsnapshotの範囲はbrowser.jsonに記録する。保存download、任意係数、complex、実機性能、公開は未確認。

保護port53478/60285/50835とtab6/7/17へ操作しない。自分のserver/tabだけcleanupし、sandbox bind/connect拒否も別の実測として残す。

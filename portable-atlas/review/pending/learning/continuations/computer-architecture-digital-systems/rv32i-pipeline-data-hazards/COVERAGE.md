# 観測範囲

|経路|照合対象|範囲・制限|
|---|---|---|
|独立sequential oracle|27比較の全32register、手計算の期待値|ADD/ADDIのみ、pipeline helperを呼ばない|
|手書きcycle表|chainの全stage、stall位置、cycle数|独自契約のnone/stall/forwarding|
|入力拒否|型、register、即値、program数、field、mode|18実行、silently coercionしない|
|故障変種|x0書込/forward、古いproducer優先、WB欠落、即値unsigned、wrap欠落、MEM待ち欠落、ID先読|8実行、差のwitnessをrawに残す。一般的なmutation scoreではない|
|IAB実表示|9fixture×3対策、chainの3比較、予測、変更、reset、source|CUAによる実操作とDOM読出し。browser.jsonに手動転記の区別を残す|
|HTTP|正常JSON、malformed/余分field/unknown/nonfiniteの拒否|一時localhostのみ。sandbox失敗も残す|
|画像|実際のUI tool capture|inline captureのみ。保存画像、path/hashを作ったとは主張しない|
|再検証|verify/route/Skill validator/hash・mtime|read-only proofを最後に書く|

実環境はPython 3.9.6、標準library、Codex IAB。ブラウザ数値はintegerなのでexact比較する。browser rawをCLI成功に代えて実表示の証拠にはしない。CLIと一致したDOM projectionのみ、比較済みのtranscription templateとして転記する。公式ISAと独自cycle契約の範囲を分ける。

保護対象の既存3server・tab6/7/17は操作しない。今回作った動的portのserverとtabだけを停止・閉鎖し、その結果を記録する。全Atlas検証、実機、HDL、一般負荷、全命令適合性、download保存は未確認。

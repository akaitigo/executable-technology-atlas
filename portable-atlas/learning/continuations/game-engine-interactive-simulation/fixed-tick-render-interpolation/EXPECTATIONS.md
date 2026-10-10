# 実行前の独立literal

20msごとに位置へ20 toy unitを足す。初期previous/currentは0。余り5/10/19msはalpha 1/4,1/2,19/20。25/30/39msの最初のtick後はprevious=0,current=20、描画5/10/19。正常はcurrent=20を保持する。次の15/10/1msでprevious=20,current=40,alpha=0,描画20。

書戻し故障は最初の描画5/10/19をcurrentへ代入。次tickのprevious=5/10/19,current=25/30/39、alpha=0で描画5/10/19。故障がtick stateを汚すことをliteralで区別する。描画の境界alpha=0はpreviousを描くため、currentと一致しないのが正常。

[oracle.json](oracle.json)は全frameの [previous,current,remainder,alpha,render,stateAfterRender,totalTicks]。整数も文字列、有理数は既約 n/d。計算実装を実行する前に固定した。可変入力7/13msの期待値は[custom-oracle.json](custom-oracle.json)。繰り返し描画だけの[25,0]故障では5→5/4へさらにstateが汚れる。複数tick [65] はprevious40/current60/render45。拒否はtrace空、部分state更新なし。

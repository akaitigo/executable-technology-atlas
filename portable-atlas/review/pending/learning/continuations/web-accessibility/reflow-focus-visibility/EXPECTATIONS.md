# 事前期待表

同じnative formを1000×800/320×800 CSS pxのviewportで比較。Browser zoomは未測定。4条件をproducer前に固定する。

|条件|横overflow|Tab順|author outline|送信の遮蔽|
|---|---|---|---|---|
|fixed-1000|なし|person,email,category,agree,send|抑制|故障パネルあり|
|fixed-320|あり|同上|抑制|故障パネルあり|
|fluid-1000|なし|同上|3px solid|なし|
|fluid-320|なし|同上|3px solid|なし|

W3C WCAG2.2 Understanding Reflow SC1.4.10 / FocusVisible SC2.4.7 (両頁Updated2026-09-06、2026-10-06JST取得)のIntentを読んで作る独自fixture。Understandingは解説であり規範そのものではない。

Tab到達、枠style、viewport外、overlayとのrect重なりは別の判定。outline0だけで全focus indicator不存在と断定しない（text caretやnative borderもあり得る）。full遮蔽はDOM幾何と実captureを併読、AX残存を見た目可視性へ外挿しない。狭幅の右側欠落は現viewportから外れる状態で、データ削除としない。文字欠落、label/controlの位置、全件存在、document/viewport/scroll寸法を保存。短いformは二次元layout例外として設計しない。

全WCAG、contrast、forced colors、touch、AT、media、zoom、全遮蔽ケースは未評価。実AT/OS設定/アプリ設定変更なし。

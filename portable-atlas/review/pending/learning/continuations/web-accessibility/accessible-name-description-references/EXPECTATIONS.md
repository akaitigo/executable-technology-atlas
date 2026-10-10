# producer前の期待表

原典：AccName 1.2 2026-10-02 Working Draft §4.2 / §4.3.2。name/descriptionは原典読解による期待、実測ではない。対象は単純native buttonとspan/pのみ。title・aria-description・循環・shadow・generated contentは除外。

|条件|期待name|期待description|理由|
|---|---|---|---|
|visible|保存|空|内容から名前|
|aria-label|送信|空|aria-labelが内容より優先|
|labelledby|優先ラベル|空|有効なlabelledbyがaria-labelより優先|
|describedby|保存|端末へ保存|説明は名前を置換しない|
|hidden-label|非表示ラベル|空|直接参照hiddenは名前へ|
|hidden-description|保存|非表示の補足|直接参照hiddenは説明へ|
|unreferenced-hidden|保存|空|参照なしhiddenは除外|
|visible-ref-hidden-child|表ラベル|空|可視参照元のhidden子は除外|
|hidden-ref-hidden-child|隠し親 隠し子|空|hidden参照元のhidden子も含む|
|reference-order|第二 第一|空|IDREF順|
|broken-reference|代替名|空|有効IDREFなしでaria-labelへ|
|unnamed-operable|空|名前を付ける必要|操作できても名前は空|

DOM/textContentからcomputed AXを推測しない。IAB role queryは名前条件の観測として記録し、OS AX propertyや実AT音声とは分ける。description公開APIがなければ全条件UNOBSERVED、空文字としない。未知descriptionをname-query結果でpassにしない。実clickによるカウンターと名前の適切さは別の判断。予想誤りは保持。

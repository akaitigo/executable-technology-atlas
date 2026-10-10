# 有限coverage

|問い|証拠|範囲|
|---|---|---|
|受信EOF後に逆方向送信できるか|B recv EOF時tx=open→B sendall成功→A reply+EOF|専用AF_UNIX streamのみ|
|EOFを両方向完了と誤解するとどうなるか|故障対照18件、reply0bytes+EOF|意図的返信省略、OSの故障ではない|
|正常終了と不完全frameを分けるか|9fixture×2方式×2幅、完全/partial header/partial body/empty/0/17/trailing|1〜16bytesの単一frame|
|chunkで意味が変わらないか|合計bytes照合、81合成分割|6bytes以下は全分割、最大fixtureは単体/bytewise/全2分割、無限分割ではない|
|timeoutと実行失敗を分けるか|未送信pairのB.recv timeout0.02s、閉じたB.recv EBADF各1実測|他OS故障、close失敗、上限到達は未実測|
|資源は終端で閉じたか|全38pairのfinally close、fileno=-1|worker無し、強制thread停止無し|
|誤実装を検出するか|header短縮、17許可、partial受入、trailing無視、endian反転、reply長さ0の6mutant|実APIの全fault injectionではない|
|元学習道筋との対応|§1受信方向EOF・§6実験1の一部を実stream双方向へ拡張|元案全部やTCP実測の完了ではない|

raw.jsonは上書きしない。UIは原票を読んだ観測で、新しいsocket実行とは区別する。スクリーン画像はinline実captureのみで保存画像hashを主張しない。global/index/既存教材は変更しない。

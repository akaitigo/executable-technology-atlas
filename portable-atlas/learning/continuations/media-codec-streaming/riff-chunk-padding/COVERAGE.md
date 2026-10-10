# 増分と未網羅

実行済み：実classicRIFF mono16 fixture、3-byte JUNKとpad1、even JUNK4/pad0、sample不変、pad省略誤読、RIFF宣言全長超過、data宣言境界超過／短data、pad欠落、実wave read/exceptionとstrict契約の分離。

未網羅：RF64/BW64、WAVEFORMATEXTENSIBLE、fmt拡張、圧縮codec、複数data/list/nested chunks、seek、stream入力、汎用format適合、安全性、音質、再生clock、配信。

次の有限実験（未実施）：

1. fmt拡張を別fixtureで明示受理／拒否契約にする。[WAVEFORMATEX](https://learn.microsoft.com/en-us/windows/win32/api/mmeapi/ns-mmeapi-waveformatex)
2. 複数data chunkやLISTを小容量fixtureで比較し、結合／拒否方針を先に固定する。[Microsoft RIFF chunks](https://learn.microsoft.com/en-us/windows/win32/xaudio2/resource-interchange-file-format--riff-)
3. 専用62-byte fixtureを各byte境界で切り、strict拒否と実wave read/exceptionの有限表を作る。[wave readframes](https://docs.python.org/3.9/library/wave.html#wave.Wave_read.readframes)

元coverage/Portalはread-only。Core/fullGateや他Subject全体は評価しない。

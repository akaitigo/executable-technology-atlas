# pilot品質gateと推定拒否

|ĥ|²と正規化residualの独自gateで、合成I/Qの複素gain推定を採用するか判断する。naiveは非0gainなら品質にかかわらず逆補正する。拒否は復調未実施・BER=null・compared_bits=0。期待どおりの拒否を成功受信に数えない。

整合した逆位相pilotは|ĥ|²=1・residual0で通過してもpayloadを4/4誤る。低residualはpilotへの整合だけで、正しい位相やpayload無誤りの保証ではない。真のpayload bitsはreceiverに渡さず別harnessだけが照合する。

このディレクトリで:

```sh
python3 -B runner.py
python3 -B test_negative.py
python3 -B checker.py
python3 -B server.py --port 0
```

serverのURLを開き、採否と誤りを予想→比較する。scaleはpilotのmagnitudeを変え、直交noise追加は推定gainを保ってresidualを変える。閾値も別々に変更できる。図のI/Q点、gate2軸、採否、payload復調、harness誤りを辿ってから答えを読む。全入力変更で答え/raw/図を消し、保留旧結果は無視する。

入力の整数もJSON文字列にする（例 `"1"`）。JSON数値 `1` は契約外。分数は `"1/2"` の形式。

PDFを表示できない環境では画面のMIT HTML原典入口を開く。

通常CLIはread-only。原票更新だけrunner/checker/test_negativeの明示 `--record`。currentは合格rawだけを指す。receiver実subprocess stdinはknown pilot、received pilot/payload、閾値だけ。rawと別audit/receipt、独立normal equations/energy identity、実装前の手literalを照合する。I/Qは固定合成4symbol、Fraction CPU計算。波形streamや実clock/実RFではない。

[契約](EXPECTATIONS.md)、[根拠](SOURCES.md)、[範囲](COVERAGE.md)、[Skill](skills/atlas-pilot-quality/SKILL.md)、[QA](QA.md)。telecom-sdr README次案2の独立continuation候補。MIT所定gate/MAP、規格、実RF、確率BER一般、機器性能は未実証。Subject/Atlas completeやaccepted数は主張しない。公開・commit・push・global installは未実施。

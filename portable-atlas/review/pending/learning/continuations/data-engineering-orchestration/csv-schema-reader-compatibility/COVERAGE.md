# 有限契約の範囲

最大1024 UTF-8 bytes、header+1..4 data records、最大5列。writer-v1/v2のbaseは実DictWriter生成byteと固定原票の一致を確認してからreaderへ渡す。literalでは固定fixtureと編集入力を読む。

required欠損、duplicate/empty/unknown header、extra/missing cells、空のrequired数値、小数字面を拒否。v1の未知列拒否とv2の既知optional欠落defaultを別policyとして比較する。列順変更は名前読取で受理する。故障位置読取は同型値を入替えてparse成功する。

raw CSVのSHA、stdout、stdin、source SHA、UTC、exit codeを結ぶ。実UIの対応図・record表は子プロセスstdoutから生成する。推論した一般互換やschema標準の適合、本番data契約、分散scheduler、更新適用、旧incremental教材やweb/api evolutionは範囲外。

actual file rejected時のrecordsは解析経過であり、typed_rowsは空。未知headerで停止した場合はfield対応を作らない。syntaxエラーはcsv.Error、他の契約拒否は独自reasonで示す。

失敗履歴と修復、UI検査、cleanupはqa、凍結原票はobservations、新規unitのみのbindingはartifact-index。受理reviewと全体gateは中央担当。

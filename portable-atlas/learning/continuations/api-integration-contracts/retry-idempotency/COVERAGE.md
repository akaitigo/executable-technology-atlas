# 継続単元のcoverage増分

入口97の既存GET教材は変更しない。増分はPOSTの業務commit後・応答前の切断、結果不明から1回の再送、keyなし重複、同一key/bodyの結果再生、異なるbodyの409、SQLite業務rowとledgerの同一transactionを実行で確かめる範囲。

未実施: TTL、key scope/auth、並行競合、複数server、crash recovery、外部副作用、本番exactly-once、任意JSON/schema/入力防御、一般的retry policy。HTTP内側endpointはrunnerが作る固定合成入力だけで試した。原票checker成功はこれらを証明しない。次の4問いはREADMEにある。

# producer実行前に固定した離散tick契約

到着eventはID0/1/2、tick0/1/2。tick0..5を順に計算、同tickはarrival→受入/drop→consumer→tick末snapshot。consumerはtick3以降、毎tick最大1IDをFIFOで取り出してそのtickのsnapshotで完了記録。実1tickの物理処理時間ではない。実sleep/IRQ/RTOSは使わない。

capacityは待機queueのID数、0..3整数（bool不可）。正常はreject-newest: 満杯で新IDをdrop、既存queueを変えない。capacity2はevent2だけdrop、0はtick3、1はtick4完了。capacity3は0/1/2をtick3/4/5完了。capacity0は全drop、emptyは到着/受入/完了すべて0で別case。

slot-overwrite故障はcapacity2指定を単一slotで誤実装し、受入申告した古いIDを次到着で上書きする。tick1で0、tick2で1を喪失し、2だけtick3完了。到着3、受入3、drop0、完了1、accepted済喪失2。通常の満杯拒否dropと、受入後喪失lostを同じcountにしない。

イベントlist長0..3、event fieldはid/tick厳密一致、両方boolを除く整数0..2、ID/tick重複なし、tick昇順。未知mode、slot modeのcapacity2以外、不正capacity、event構造/ID/tick/list/順序を拒否して計算を始めない。JSON構文拒否もINPUT_REFUSED。拒否/実行失敗のtimeline/countsはnullで、正常0と混同しない。

[手書き表](oracle.json)は6正常/故障case×6tickのqueue・arrived/accepted/drop/processed/lost ID・累積完了tickと最終countを固定。11拒否+実RuntimeErrorの18case。独立oracleはqueue関数/producerをimportせず、literal tick行と集合の整合を照合する。

全予想controlで成功比較→答えdetailsを開く→その欄だけ変更を最初から実IAB確認。新予想/他欄を保持、旧比較/raw/timeline/count/答え本文を消しdetailsを閉じる。条件resetは両予想/JSON上書きを消す。拒否は予想と理由を比較でき、実Errorは正常答えなし。

旧応答は実HTTPで既に受信したpayloadの描画適用だけを保留して対照にする。条件/予想変更後のversionと違う保留payloadは受取操作で破棄し、最新結果を変更しない。通信遅延を測定したとは呼ばず、sleepを用いない。

通常コマンドはread-only。明示recordだけ新UTC/UUID raw、実child attempt/exit/stdoutとsourceSHAを保存。旧raw保持、想定外実行失敗はcurrentへ昇格しない。実IRQ/SMP/memory order/WCET/deadline/Safetyを保証しない。

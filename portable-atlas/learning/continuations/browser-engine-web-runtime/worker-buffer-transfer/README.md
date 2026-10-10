# WorkerとArrayBufferのclone / transfer

[既存Subject README](../../../subjects/browser-engine-web-runtime/README.md)の未実施E3「worker有限計算とmessage/transfer」を狭く実装する独立教材。元のevent-loop教材や入口は変更していない。

先に元Subjectのevent-loop教材でtask/messageの順序を読み、ここではWorker境界で渡すデータと所有状態に絞る。[関連：静的名前解決教材](../../programming-languages-compilers-runtimes/static-name-resolution/README.md)は宣言IDと値の対応を扱う。名前の束縛とbufferの所有は別の契約として比較し、片方の成功をもう片方の保証へ使わない。

規則→送信側の予想→条件変更→Workerへ送信→正常/拒否比較→一次仕様・コード・raw→答え→実務判断の順で進む。独自の3固定fixtureのみ。各実行が所有するDedicated Workerをfinallyでterminateする。

## 事前期待と実験

| 入力 | 送信側ack後 | Worker受信・変更 | 最終data件数 |
|---|---|---|---|
| clone [1,2,3,4] | length4、bytes元のまま | length4 / sum10、変更後[9,2,3,4] | 1 |
| transfer [1,2,3,4] | length0、Uint8Array再生成TypeError | length4 / sum10、変更後[9,2,3,4] | 1 |
| 同bytes＋関数、clone | DataCloneError、length4と元bytes保持 | data ackなし | 0 |

手書き表 `oracle.json` はブラウザ実行前に作成。producerはoracleをimportせず、Uint8Array/Worker/postMessageで実測する。正常2ケース、期待serialization拒否1ケースを分ける。timeoutやWorkerエラーは別のEXECUTION_FAILUREであり、期待拒否の成功証拠にはしない。

各Workerのprobe-before ack（count0）を受けてから送信する。実postMessageの直後とdata ack後で送信bufferを読む。Workerはdata IDを記録しbytesを合計して先頭を9へ変更してackを返す。関数拒否は同期例外名を記録し、同channelに続けたprobe-afterのackでcount0/ID一覧空を確認。data/probeのIDはrun UUIDで区別。各request最大5000msでtimeoutを明示する。無受信を短sleepだけで断定しない。この有限試行のserialization拒否を、あらゆるnetwork/processで未到達を証明する手法へ一般化しない。

## 原票と再現

このdirectoryで `python3 -B server.py`。127.0.0.1:0を所有し競合を避ける。sandbox bind失敗が出る場合は失敗を保持して同じloopback previewをhost許可で起動。IABで3条件を選択し予想→実行→比較して、必要な新原票は「新原票を保存」で明示採取する。POST /recordは固定fixtureと現source SHAを確認し、fresh UTC directoryのraw.jsonへ保存する（他pathへ書けない）。通常検査は保存しない。EXECUTION_FAILUREはphase/errorと部分rawを表示し、oracle未判定・正常/期待拒否は未確認とする。「失敗原票を保存」はPOST /record-failureでobservations/failures/UTC/failure.jsonへ別保存し、成功原票やDataCloneError確認の集合へ混ぜない。

`python3 -B check.py` はPython stdlibだけで全保存runをread-only検査する。独立のbytes合計と所有状態モデル、ID付きbefore/data/after ack・件数・関数拒否の例外とack無発生を、手書き表と原票へ照合。producerやUIから期待値を生成しない。5種の証拠改変を拒否する。旧sourceはobservations/20261005T122916804863Z-failure-repairの*.beforeに保持し、旧原票はその厳密SHAへ照合する。明示QA faultの失敗記録は同directoryのcheck-failure.pyで別検査する。QA専用probe保留/解放は30000msに延長した専用producerで検証し、通常5000msの正常証拠にはしない。`python3 -B skills/atlas-worker-buffer-transfer/route.py worker-buffer` は同検査と保存rawへroute。未対応入力はexit2。

原票にはUTC、browser userAgent/platform、fixture、送信前/直後/ack後状態、Worker bytes/sum、例外、ID、ack、操作順、終了、6source SHAが入る。qa.jsonに実IABの原票保存ackとUI操作要約、verification.jsonにsource/artifact SHAと通常検査前後hash/mtimeを記録。captureは実画面をツール表示したとき、保存できない制約を明示し再構成画像を作らない。予想変更は選択値を保持、条件変更は予想unknownへ戻し、いずれも結果/trace/raw/答えをclearしてgenerationで古い結果を破棄。

## 一次仕様と観測の限界

2026-10-05に[HTML Safe passing of structured data](https://html.spec.whatwg.org/multipage/structured-data.html) §2.7.2 Transferable objects、§2.7.3 StructuredSerializeInternal（ArrayBufferのcopyとcallable拒否）、§2.7.7 StructuredSerializeWithTransfer（detach）、[Worker postMessage](https://html.spec.whatwg.org/multipage/workers.html#dom-worker-postmessage)を確認。生きた仕様へのlocatorで、全仕様の適合を証明していない。文章/コードを転載せず、固定fixtureを独自実装した。

観測はbytes・所有状態・ackだけ。速度比較、物理zero-copy、OS process/thread配置、engine全実装、sandbox保証、SharedArrayBuffer/Atomics/ServiceWorker、cross-browser適合を主張しない。任意コード/任意URL/任意message payloadは受け付けない。Core/fullGate、依存追加、commit/push、公開・課金・設定変更は未実施。元Subject/Atlas全体の完了ではない。

## 次の未実施案

1. Workerからbufferを再transferして返す。同じ4bytesで所有状態の往復とWorker側detachを比較。[StructuredSerializeWithTransfer](https://html.spec.whatwg.org/multipage/structured-data.html#structuredserializewithtransfer)を参照。現単元はack JSONだけで返す。
2. 重複transfer list・detach済みbufferの再送。例外/送信側状態/後続probe件数を比較しserializationとtransfer失敗を分ける。同仕様のtransfer list検査を参照。現単元は関数拒否だけ。
3. SharedArrayBuffer/Atomicsは別fixtureと必要な許可・isolation条件の検討後に扱う。[HTML shared memory](https://html.spec.whatwg.org/multipage/structured-data.html#structuredserializeinternal)を参照。所有移動と共有/同期を比較する計画のみで、現在は権限・header・OS設定変更をしていない。

## setup / 再実行の失敗境界の追加検証

実行開始の共通resetは新case/予想を保持し、前の比較・raw・答え・保存対象を消す。Worker constructor/buffer setupもproducerのtry内、未生成Workerをterminateしない。失敗はphase/error/部分rawと未判定、保存導線は新しい失敗専用原票。UI側例外でも同じclearを通す。generationで各返り道の旧応答を破棄する。

observations/20261005T124701826843Z-constructor-repairは第2修正。constructorのSecurityErrorはQAが2回目constructへ明示注入する合成例外で、実OSがWorker作成を拒否した証拠ではない。前正常→再実行失敗を実IAB確認し、未生成・空比較・閉じた答え・失敗専用保存を記録。過去source/原票/QA/receiptを残し、check.pyは正確な過去source SHAへ照合。check-failures.pyは失敗集合を独立照合する。

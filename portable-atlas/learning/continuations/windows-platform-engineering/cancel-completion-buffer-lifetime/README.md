# cancel要求とcompletionの間は、まだoperation Aの寿命

[元Windows](../../../subjects/windows-platform-engineering/README.md) / [未教材async coverage](../../../subjects/windows-platform-engineering/COVERAGE.md)次2から、cancelとbuffer/OVERLAPPEDの再利用境界だけをMac Python標準ライブラリの有限模型にします。旧quotingとは別概念です。実Win32 API/Windows/VM/実memory corruptionは未実行。

前提は非同期operation、要求と完了、所有者、世代番号。quoting→このasync寿命→実Win32/IOCP/driver/COM/wait/handle（未制作）の順で読む。

~~~sh
python3 -B runner.py --record
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py inspect
python3 -B route.py lesson
python3 -B preview.py
~~~

loopback動的URLでreuse許可/旧completion干渉/最終世代を予想→実処理→原典/source/raw→答え。入力はsubmit先頭＋cancel/reuse/complete各一回の6順列、success/aborted、初期世代1..9、ASCII payload1..40。順序/結果/世代/payloadを編集して再比較する。新値を保持し、入力/予想変更は旧status/trace/答え/rawを空にしてdetailsを閉じる。条件変更は予想も空。旧非同期応答は世代で破棄する。

| submit→cancel→reuse→complete | reuse | 最終buffer | 干渉 |
|---|---|---|---|
| guarded / success | 拒否 | g1 / A-result / success | false |
| guarded / aborted | 拒否 | g1 / empty / aborted | false |
| cancel-release-fault / success | 許可 | g2 / A-result / success、owner失効 | true |
| cancel-release-fault / aborted | 許可 | g2 / B-data / aborted、owner失効 | true |

cancelはpendingを完了へ変えません。正常はowner Aを保持。故障だけcancel時にownerを空にし、同slotを新世代/applicationへreuseします。A completionのunguarded callbackが現在slotのstatus/ownerへ触るため旧世代からの干渉を記録。successだけoldPayloadへ更新、abortedでは新payloadを保持しstatus/ownerだけを更新する **説明模型**。aborted後の実DMA書込みやWindowsが必ずこの壊れ方をするとの主張はありません。

completion前reuse拒否は自動retryしません。complete→reuseなら新世代のpayload/ownerが残り干渉なし。complete後cancelはNOT_PENDINGで新ownerを手放しません。completion abortedは実process失敗ではなく正常模型入力で、cancel前のabortedも合成completion結果として受け付け、cancel要求との因果を保証しません。

[事前literal所有table](oracle.json)はproducerより先に各operationのbuffer世代/owner/pending/cancel/status/payload/干渉と最終状態を固定。[model](model.py)は状態遷移。[独立checker](checker.py)はproducerをimportせず、各actionの順序位置から閉形式で状態を作り、literalも照合。[execute](execute.py)でmodel＋独立auditを実子process起動し、input/UTC/argv/exit/stdout/stderr/sourceHashesを原票へ。UI JSは模型を代算しません。

不正order/duplicate/bool世代/unknown completion/payload型/unknown policyはREFUSED exit2、JSON破損は実decode失敗exit3/stdout空。audit/HTTP失敗・旧応答は正常stateと別扱い。recordのみ新UTC保存＋CURRENT、旧raw上書きなし。default runner/checker/routesは全module SHA/mtime不変。UI処理はメモリreceiptのみ、30000byte上限、qaDelay=2000はtransportの旧応答QAだけ。[QA](QA.json)で実IAB/capture/検証/所有資源終了。

Microsoft [Canceling Pending I/O §Cancellation Considerations/Canceling Asynchronous I/O](https://learn.microsoft.com/en-us/windows/win32/fileio/canceling-pending-i-o-operations)でcancel要求が取消し成功を保証せず、成功/取消しcompletionまでOVERLAPPEDを再利用しない点を確認。[ReadFile lpBuffer/Remarks](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-readfile)でbufferを完了まで使用/再割当/解放しない点を確認。CancelIoEx個別API頁は今回のweb取得がInternal Error、本文確認済みの上記2頁に根拠を限定します。

実Win32、handle/IOCP/driver cancel実装、VM/native toolchain、実bufferの安全性、COM/wait/event/refcount、実競合/性能/取消し期限保証は[未教材](COVERAGE.md)。旧unit/Portal/shared設定/Core/fullGate/install/公開/commit/pushは対象外。全Windows Subject完成ではありません。

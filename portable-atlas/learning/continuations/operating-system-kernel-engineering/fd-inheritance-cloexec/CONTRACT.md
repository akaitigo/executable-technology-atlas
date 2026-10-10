# Atlas：fork・exec と FD_CLOEXEC の契約

実装前に固定した 4 条件の教材です。分野は OS・kernel engineering、既存 COVERAGE の「次1 fork/exec と dup/CLOEXEC」に対応します。専有先はこの独立ディレクトリだけです。元 OS 担当の現在の稼働は未確認であり、元リポジトリへ統合しません。


正式な分野目標は `2026-10-06/task-8/atlas-97-field-goals-ja.md` 第11「OS・カーネル工学」（161–170行）です。今回の4条件は168行の dup と CLOEXEC の次手順へ対応します。メモリー、同期全般、耐久性の判断は既存教材・未対応範囲へ分けます。

## 到達目標と前提

FD はプロセス内の番号で、番号と参照先は別です。fork で子ができることと、exec で同じ PID の実行プログラムが切り替わることを区別し、FD_CLOEXEC（exec 時にその FD を閉じる印）が継承に与える差、印の設定漏れを判断できることが目標です。前提は process/PID、FD、read/close、子の終了を wait で回収することです。

原典→参照実装→保存結果→Skill の案内をつなぎます。Python 3.9 の os 文書、手元 SDK の fork/execve/fcntl/dup man、Apple の保存版 man を参照します。保存版の契約説明と現在の Mac の測定は分けます。POSIX 本文の取得失敗は親からの記録、Apple fork の取得失敗は今回の記録として保持し、取得できたとはしません。

## 実装より前の固定期待

入力ファイルは自己所有の一時ディレクトリに置く `ATLAS-FD` の 8 バイト。各条件で新しく作ります。下表の on/off は FD_CLOEXEC の値です。FD 番号・PID・dev/ino の実数は固定せず、同じ条件の同じ実行内で比較します。

| 条件 | 元 FD / 複製 FD の印 | fork 後の子 | exec 後の子 | wait 後の親 |
| --- | --- | --- | --- | --- |
| guarded_single | on / なし | 元の対象あり | 元は EBADF | 元の対象あり |
| unguarded_single | off / なし | 元の対象あり | 元の対象あり。渡さない意図に対して設定漏れ | 元の対象あり |
| dup_original_guarded | on / off | 両方の対象あり | 元は EBADF、複製は対象あり | 両方の対象あり |
| dup_duplicate_guarded | off / on | 両方の対象あり | 元は対象あり、複製は EBADF | 両方の対象あり |

Python の `os.dup` を実際に使い、返った直後の複製 FD が non-inheritable（exec で閉じる設定）であることを記録してから、条件ごとの印を `fcntl(F_SETFD)` で設定します。これは Apple/POSIX の C の `dup(2)` が新 FD の印を解除する契約とは別の API です。C の dup を実行したとは扱いません。

各観測は fstat の `(st_dev, st_ino)` を準備した対象と照合します。一致した場合だけ pread の 8 バイトを読み、同じ FD 数字が別対象へ再利用されていたら `different-target` と記録して固定期待の成功にしません。`EBADF` は期待した拒否、fork/exec/通信/timeout の例外は実行失敗、設定漏れによる継承は観測できた負例として分けます。PID は fork 前後で異なり、子の exec 前後では同じ、親は子の wait 後も同じです。

ファイル identity の一致だけで open file description（開いた参照が持つ offset 等の状態）の共有を証明したとはしません。offset の相互作用は測定対象外とし、pread で位置を動かさずに読みます。子への制御用 pipe は測定対象 FD と分け、子が exec 後の記録を親へ返すため明示的に継承可能にします。

## 実行・失敗・受入

標準 Python 3.9.6 / Darwin arm64、既存 API だけ。最大 1 owned child、4 条件を逐次 1 batch、各子 2 秒・batch の観測 10 秒上限、低優先度 nice 10 以上。観測の期限と後片付けを分け、停止した子の回収待ちには別に最大 1 秒の猶予を設けます。回収できない場合は失敗とし、次の条件を開始しません。期限通知で後片付けの記録が失われないようにし、個々の回収失敗と受信途中の記録も残します。自分の child のみ timeout 時に停止して wait、すべての owned FD と一時ファイルを回収します。OS 設定、他プロセス、SDK、Docker、公開は変更しません。初回失敗も別 attempt に完全出力とともに残します。

受入条件は、固定 4 条件・対象 identity・全 8 バイト・印・PID 関係・3 件の期待 EBADF・設定漏れ 1 条件・親の参照残存・終了回収の独立照合です。保存結果の欠落/改変を検証が拒否することも確認します。元実験を不用意に再実行せず、UI は保存結果だけを読みます。

画面は「条件と予想→時点再生→正常/異常比較→原典とコード→答え→限界」の順です。条件/予想/reset で古い答えを消し、取得失敗・遅延応答を実験失敗と混同しません。矢印図は保存値を説明する模型、実画面 capture はその画面の記録です。1280/390 の実ポインター操作・実画像を確認できた範囲で別担当へ受入を依頼します。browser 枠は親の割当後だけ使います。

既存 pipe EOF・mmap・unlink/replace・hardlink の結果を参照して前提へ戻れますが、再制作・再加算はしません。マルチスレッド fork、全 OS、FD の race、offset、性能、sandbox/security 全体の保証は対象外です。全 OS の理解・網羅性・教材数を完了基準にはしません。

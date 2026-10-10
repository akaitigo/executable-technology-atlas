# Atlas：原典と測定の境界

原典の契約、Python API の設定、今回の Mac の測定を分けて読みます。取得記録とローカル文書のハッシュは [sources.json](sources.json) に保存しています。

| 原典 | この教材で確認する箇所 | 適用の境界 |
| --- | --- | --- |
| [Python 3.9 os：dup](https://docs.python.org/3.9/library/os.html#os.dup) | Python の複製 FD は 3.4 以降、原則として継承不可。dup2 には別の inheritable 引数がある | 閲覧版は 3.9.25、実行したのは手元の 3.9.6。C の dup と同一契約にはしない |
| [Python 3.9 os：fork](https://docs.python.org/3.9/library/os.html#os.fork) | 親への子 PID と子への 0 の戻り値 | この教材は単一スレッドの小さい所有プロセスだけ |
| [Apple 保存版 execve(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/execve.2.html) | 開いた FD と close-on-exec、PID を保つプログラム切替え | 古い保存版の契約説明。現在の実装全体の証拠ではない |
| [Apple 保存版 dup(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/dup.2.html) | C の複製 FD と印の扱い | C の dup 呼出しは今回実行していない |
| [Apple 保存版 fcntl(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fcntl.2.html) | FD の印の取得・設定 | F_GETFD / F_SETFD と、別の file status flags を混同しない |

現在の手元 SDK の `usr/share/man/man2/fork.2`（60–69行）は、子が FD のコピーを持ち、同じ下位対象を参照する契約を説明しています。`execve.2`、`fcntl.2`、`dup.2` も読取り、パスと全内容のハッシュを記録しました。offset の共有はこの契約に含まれますが、本教材の実験では offset の変化を測っていません。

Apple fork の web 読取りは今回 1 回 internal error、親担当の POSIX fork/exec/dup 読取りは各 1 回 403 でした。繰返し取得せず、成功した公式文書と SDK の man で進めました。取得できなかった本文を読了扱いにはしていません。

実測は macOS 26.1 / arm64 / CPython 3.9.6。8 バイト、4 条件、同時 1 子プロセスです。保存版の文章や図から現在の測定結果を創作せず、実行ログと [固定期待値](expected.json) の一致を確かめます。

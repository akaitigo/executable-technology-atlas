# 原典と取得限界 / 2026-10-06

[Python公式os](https://docs.python.org/3/library/os.html)、os.remove / os.unlink / os.replace / os.fsync（現在取得本文は3.14.8、実行Pythonの版は原票environmentで別記）。Unixのunlinkはnameを消し、使用中のfile storageの解放は参照終了を待つ。replace成功時のrenameはPOSIX要件としてatomic、異なるfilesystemでは失敗し得る。fsyncはFDの書込み同期APIだが、本教材はそのreturnのみ観測し、電源断後の内容を確認しない。

[POSIX unlink](https://pubs.opengroup.org/onlinepubs/9799919799/functions/unlink.html)、DESCRIPTIONの最後のlinkを削除したときのopen参照寿命。[POSIX rename](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html)、DESCRIPTION/RATIONALEのatomicな名前変更。この2直URLはweb取得Internal Error。公式検索でOpen Groupのunlink旧版とrenameの抜粋は取得したが、現在版全文検証とは扱わない。9699919799 unlink、000095399 renameの検索結果から1回ずつ本文取得も試しInternal Errorだった。evidence/source-acquisition.jsonに限界を保存。

Python公式本文は取得済み。POSIX全文を未取得のまま全FS/全OSを保証しない。第三者本文や図の複製は保存しない。unlink/replace後の有限観測は本Macの実OS実行原票による。

[既存COVERAGE](../../../subjects/operating-system-kernel-engineering/COVERAGE.md) 次4から派生。既存pipe/mmap原票を本実験の証拠へ流用しない。

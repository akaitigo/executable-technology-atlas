# 一次資料locatorと実装binding

確認日2026-10-05。公式規格の検索索引と、本文取得を区別する。実験の正本は有限入力・raw・独立reader-state oracle。製品filesystem全体の保証へ転用しない。

| ID | 一次資料locator・節 | 今回の実装との対応 / 確認状態 |
|---|---|---|
| RENAME | [POSIX Issue 8 rename()](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html), DESCRIPTION / RATIONALE | [experiment.py](experiment.py)のos.replace前後。[oracle.py](oracle.py)のpath新版/既存reader旧版。公式検索索引確認、直接openは403。名前の置換はruntimeの可視性の話。 |
| DURABILITY | [POSIX Issue 8 Rationale for Base Definitions](https://pubs.opengroup.org/onlinepubs/9799919799/xrat/V4_xbd_chap01.html), directory atomicity / durability discussion | file syncとrename、directory syncを分ける。検索索引確認、直接openは403。今回power lossを起こさず、durabilityを証明しない。 |
| PY | [Python os.replace / os.fsync](https://docs.python.org/3/library/os.html#os.replace), replace atomicity / fsync flush | Web本文確認。実行はPython3.9.6。buffered writerはflushしてからfsync、readerはunbuffered。新規tempはtargetと同じowned directoryに作る。 |
| MACSYNC | [Apple fsync(2) manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fsync.2.html), fsync / F_FULLFSYNC discussion | Web本文確認。歴史的manualのlocator。fsync成功をdevice cacheや電源断の永続性保証と呼ばない。F_FULLFSYNCは今回呼ばない。 |
| APFS | [Apple File System Reference](https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf), containers / object map / snapshots / clones | 公式PDF取得確認。block-level copy-on-writeの次学習用。今回filesystem typeやphysical block共有を測定しておらず、APFS clone実験ではない。 |
| VFS | [Linux filesystem documentation](https://docs.kernel.org/filesystems/index.html), VFS / inode / dentry / address space / journalling | Web目次確認。pathとopen fileの違い、page cache、metadataとjournalingへ進む入口。今回Linux kernel実装は実行していない。 |

[入力](cases.json)→[実行raw](evidence/raw.json)→[独立oracle](oracle.py)→[run](evidence/run.json)のinput/source/artifact SHA-256→[integrity](evidence/integrity.json)を辿る。[初期実装failure](evidence/bootstrap-failure.json)は修正前の実エラーとtemp cleanupを保存したもので、正常観測として扱わない。

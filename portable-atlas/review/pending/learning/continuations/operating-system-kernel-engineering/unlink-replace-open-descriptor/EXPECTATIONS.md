# 先固定した契約

入力は厳密にold_payload/new_payload/fsync/modeの4field。payloadはASCII（codepoint0〜127）文字列各0〜512 bytes、fsyncはbool、modeはcompare/missing-source/closed-fd。任意path、追加field、unicode、型不正、513bytesを操作前に拒否しmutation_started=false。専用TemporaryDirectory内で固定名live/prepared/missingだけを使う。実user fileは対象にしない。

compareは独立したtempdirで3経路を実測。unlinkはprepared状態→os.unlink(live)→after_unlink。replaceはprepared状態→os.replace(prepared,live)→after_replace。gapはprepared状態→os.unlink(live)→gap_after_unlinkの同期reader callback→os.replace(prepared,live)→after_replace。callbackは1回でsleep/競合確率なし。単一replaceのbefore/after観測から任意raceや全FSの原子性を証明しない。

両準備ファイルを実os.openで作成しwrite、FDを維持する。各rowでold_fd/new_fdをlseek(0)→bounded read→EOF確認→fstat。live pathnameはstat→新規open/read/fstat→close（不存在はstat/openそれぞれENOENT）。prepared pathnameはstat。identity=(st_dev,st_ino)は同一run内だけold/newに対応付け、runを跨ぐ数値比較をしない。同内容でもidentityは別。実syscall logとFD番号は原票に残すがtemp絶対pathは保存しない。

手表hand-trace.jsonに、phase、old FD内容role/nlink、pathname role/nlink、新FDrole/nlink、prepared path role、pathname errorを固定。正常のold FDは常にold bytes。unlink/replace後はold nlink=0、path再openはunlink後ENOENT、replace後new bytes。source preparedの名はreplaceでなくなるがnew FDは維持する。

fsync=trueなら準備中にold/new FDへ各1回os.fsyncを呼びRETURNED/exceptionを分ける。falseはSKIPPED。directory fsync、F_FULLFSYNC、停電/crashを試さずdurability='UNOBSERVED'。visibilityとfsync成功を耐久性へ読み替えない。

missing-sourceは存在しない専用missingからliveへのreplaceを実呼出しENOENTを捕捉、pathはoldのまま。closed-fdはoldFDをclose後、割当操作を挟まずos.readしてEBADFを捕捉。これはOS_EXCEPTION_OBSERVED exit4でありcompare正常/故障gapとは分ける。producer-failureは--failで準備後にRuntimeError、EXECUTION_FAILED exit3として部分traceとcleanupを保持する。不正入力exit2、正常exit0、予期しないOS失敗exit5。cleanupはfinallyで所有FD close、直後fstatのEBADF確認、tempdir削除を観測する。

独立oracleはproducer/OS helpersをimportせず手表とpayloadから正規化した全rowを構成し、raw inode対応・FD読取長・EOF・stat/fstat対応・syscall証拠・cleanupを別照合する。実行値を期待表へコピーしない。fixtureの空/同内容/異内容/512境界と4追加条件を扱う。全FS/Windows、kernel内部、実disk耐久性、poll、pipe/mmap、権限設定変更は対象外。

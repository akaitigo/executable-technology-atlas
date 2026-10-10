# 原典と確認状態

- [Apple flock(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/flock.2.html): 本文確認。advisory lockは協力するprocessのためのもの。LOCK_EXとLOCK_NB、競合時EWOULDBLOCK、fileへのlockという契約を今回の実測と照合。archive文書であり現行macOSの全差分の保証ではない。
- [Python fcntl.flock](https://docs.python.org/3/library/fcntl.html#fcntl.flock): 本文確認。file descriptorを渡すUnix wrapper。手元Pythonのversionは[原票](evidence/raw.json)に記録。最新docsの新機能は使わない。
- [POSIX rename](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html): 今回fetch403、locator保持。本文未確認として扱う。第1単元の原票や原典状態は変更しない。
- [Python os.replace](https://docs.python.org/3/library/os.html#os.replace): 本文確認。成功したrenameはatomicという契約（os.replace節）。別candidateを完成させて同一directoryでreplaceする今回の実装は[worker](worker.py)参照。

作者の実験契約: 初期bytes `0\n`、writer A/Bが各+1、pipeによる応答barrierで手順を制御。実行前の[手順と独立期待値](oracle.json)はworkerを呼ばない。lockfileはreplace対象とは別で、両writerが同じfileをopenし、read前の取得からrename後の解放まで保護する。

原典からの判断: advisoryなので全writerが同じ規約に参加する必要がある。実測は3つの指定順序であり、任意scheduleやfilesystemに一般化しない。atomic visibilityはcheckpointで完全bytesが見えた事実と、既存第1単元のpath/FD観測に限定。継続reader stressやdurability証明ではない。

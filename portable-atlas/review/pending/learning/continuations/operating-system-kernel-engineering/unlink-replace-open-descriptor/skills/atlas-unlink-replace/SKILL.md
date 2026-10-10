---
name: atlas-unlink-replace
description: このMac有限教材でunlink・単一replace・多step gapとopen済みFDを実原票から比較する。実user fileの操作やcrash durability検証には使わない。
---

このSkillの2階層上を基点にEXPECTATIONS.md、hand-trace.jsonを読んで予想する。python3 -B runner.py / route.py / checker.pyは通常read-onlyで、測定用TemporaryDirectoryだけを毎回作成・回収する。server/UIの検査は所有するserver/tabに限定する。

pathname再open、old FD、new FD、prepared名を別々に追う。inode数値の比較は同一runのidentities対応だけ。内容同一でもidentityを同一と扱わない。gapはunlinkとreplace間の同期callbackでありrace stressではない。fsync RETURNEDをcrash durability成功へ読み替えない。

OS_EXCEPTION_OBSERVED、INPUT_REFUSED、EXECUTION_FAILED、正常OBSERVEDを分ける。不正入力は操作前のmutation_started=falseを確認。原票更新は明示--recordのみ、旧証拠を保持する。oracleはproducer helpersを使わない。全traceとsyscall/cleanup証拠を照合し、不一致は保持する。

SOURCES.mdのPOSIX直URL全文取得限界を隠さない。任意path/実user fileを入力に追加せず、既存pipe/mmap/他候補/global/indexを更新しない。公開、権限変更、Windows/全FS、crash/停電のscopeを暗黙に加えない。

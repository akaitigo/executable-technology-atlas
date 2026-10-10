---
name: atlas-evidence-copy-hash-custody-boundary
description: 公開架空ASCIIの実byteコピー・SHA256と有限handoff台帳を比較する。実ログ/device/user path取得や本人認証・法的chain of custody認定には使わない。
---
元Subjectの最終未教材項目→README/NIST SP800-86 §3.1.2・4.2.2→事前literal bytes/hash/台帳oracle→実Pythonコピーへrouteする。hash一致はcopy integrity、actor/seq/ID/記録hash/from連結は別の有限整合条件。hashだけで「由来も承認済」とする故障をactor/seq/ID反例で否定する。台帳passも真正性・法的custodyの証明にしない。
合成textareaを毎回所有TemporaryDirectory内の固定名fileへ書き、shutil.copyfile/hash/1byte変化/原本再読/cleanupを実行。任意path引数なし。通常検証は全unit SHA256/mtime不変、明示recordだけfresh原票、旧失敗保存、source/artifact binding。
UIは予想→操作→正常異常→原典/source/raw→actual答え。全input/予想変更で本文・trace空、details閉、新値保持。schema拒否・台帳拒否・host失敗を分け、revisionでstale破棄。所有server/tab/tmpを除去し、有限unitをfreeze。Core/共有/OS設定/install/公開へ広げない。

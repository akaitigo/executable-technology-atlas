# 範囲

| 問い | 観測 | 残る境界 |
|---|---|---|
| unlinkとFD寿命 | old FD read/fstat、pathname stat/open ENOENT | 全OSではない |
| 単一replace | old FDと新open、source名消失、identity対応 | 任意raceの実験証明ではない |
| 多step更新gap | unlinkとreplace間に1回同期reader | 同時threadのstress測定ではない |
| fsync | 準備old/newFD各1回returnまたはskip | crash・directory fsync・F_FULLFSYNCなし |
| OS例外 | missing source ENOENT、closed FD EBADF | 正常やgapと別status |
| 所有権 | finally close/fstat EBADF、temp削除 | user任意pathなし |
| 未教材 | journaling,crash consistency,device,Windows,全FS,poll | 別実行環境と原典検証が必要 |

手表と独立oracleを先固定。実測・失敗・UIはevidenceとQA。SubjectやAtlas全体の完了を主張しない。

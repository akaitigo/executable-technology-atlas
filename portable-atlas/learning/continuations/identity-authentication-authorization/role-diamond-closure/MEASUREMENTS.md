# Atlas：保存した模型計算

[初回保存結果](observations/attempt-01.json)は5比較をcompleteで終了しました。正常集合計算2件・意図した評価拒否3件を区別し、全体の実行失敗とは扱いません。event数は4/15/12/8/2の計41です。未知ghostは訪問前に拒否、真cycleはauditor側へ進まず拒否します。

[保存値検査](observations/attempt-01.verify.json)は463項目を手期待へ照合し、7つの意味改変を各目的labelで拒否しました。検査器は模型をimport/再実行しません。一般schema拒否や未知参照edgeのtargetは今回実行していません。

root管理の対象1子はPID90764、実nice10、exit0、経過約0.075秒、reaped/groupAbsent、回収signal0です。rootはwall5秒を管理し、RLIMIT_CPUは継承値を記録しています。別のCPU時間上限や性能比較を主張しません。自動再試行0、旧教材の実験再実行0です。

実行記録の場所（教材directory基準）は `../coordination/after-183-runtime/identity-role-diamond-closure-20261007T065754469134Z/execution.json`。単体HTTP外の成功リンクとは扱いません。最初の資源観測はload8.87等でtarget未起動のholdとなり、記録を保持しました。その後、新freshで条件成立して初回targetが開始されています。未起動holdをtarget失敗/再実行と混ぜません。

成功時は直接/継承の両方にreadを残し、有効集合で重複を除去します。拒否時は診断のvisitedが非空でも、結果のclosure/permissionはnullです。[手表](HAND_TRACE.md)・[GUI範囲](GUI_VERIFICATION.md)・[現在状態](status.json)を分けて読んでください。

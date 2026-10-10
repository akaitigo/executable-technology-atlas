# Robust設計の入口・有限unit

今回:制御2setting×noise2条件/各3合成反復、目標10/二乗loss/等noise重みを先に固定。平均/分母Nばらつき/分母N−1標本分散、noise内/間、mean-only/variance-onlyのtradeoff、選択後固定settingの別fixture確認/失敗/tie/zeroを比較。独立pairwise/moment oracle、12mutant、可変actual/reset/stale/refusal、memory-only再試験と原票viewer。

未教材:SN比の各定義/zero/undefined、直交表/aliasing、dynamic signal-response、adjustment/tolerance design費用、統計独立/物理確認noise耐性、無作為化/独立反復、因果/有意性/検出力、実データ/母集団保証。robust設計をSN比だけに縮めず、入口以外は未実施。旧QE/DOE/Wilson/SQLite/global/Coreは変更しない。

次3案は未実行、自動開始しない。
1. 宣言したnoise分布/重みを変え、等重みの選択がどこで反転するかを有限表で比較。
2. signal目標を変える明示dynamic response模型で、control/noise/signalとadjustmentを分ける。
3. 一次資料のSN定義ごとにzero/undefinedとquadratic lossとの違いを検査し、別に確認fixtureを用意。実物robust試験やTaguchi全体系完了とはしない。

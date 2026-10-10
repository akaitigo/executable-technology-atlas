# 行coverageと境界mutation

[教材を開く](index.html)。整数区間の純粋関数で、弱いテストと追加後のテストを並べます。予想を選び、下端・上端・空区間のcheckboxを順に追加すると、検出した変異が1→2→3→4と増えます。元関数はどちらも正常です。

このdirectoryで既存Nodeだけを使って実行します。インストールは不要です。

```sh
node verify.mjs observations/my-new-run
node serve.mjs
```

2つ目が表示したlocalhost URLをBrowserで開きます。終了はCtrl+C。既存観測directoryの上書きは拒否します。今回のUIは固定の初回原票を読み、core.js／experiment.jsのhashを再計算して照合します。変更後の記録をUIへ使う場合はserve.mjsとUIの記録pathも合わせて指定し、再照合してください。新しいrunだけで過去原票を書き換えません。

Node runnerは4非同値変異＋1同値例に、弱い3入力／強い258入力を実行します。強いsetは3境界入力と252有限入力を含み、仕様oracleは整数集合の列挙です。別processのNode test runnerでcore.jsの実V8 coverageを採取し、stdout／stderr／runtime.jsonへ保存します。弱いsetの行coverageは100%でも、検出は1/4。強いsetは4/4。同値E1はsurviveのまま、生の分母5も表示します。

UIのcheckboxは同じJS関数を再実行します。表示する関数sourceとテスト入力・期待値はその実行に使ったものです。NodeのcoverageはBrowserで測り直さず、保存済み記録を照合します。[原票と検証記録](VERIFICATION.md)、[module用Skill](skills/atlas-software-quality-engineering/SKILL.md)を参照してください。

入力領域は整数-10〜10・lo≤hi。E1の同値性はこの領域に限ります。固定の手作り変異なので、自動変異生成やtimeout・無効変異の扱いを実証していません。行coverage／mutation scoreは品質全体や全Subject完成の証明ではありません。学習者の理解度は未測定です。

[scope.json](scope.json)と画面の表にstatic analysis、property生成／shrinking、regression、統合、fuzzing、性能・運用等を未教材として残しています。実画面QAは背景IAB＋専用localhost、Mac file URLや多Browser・支援技術は未検証。前の二分探索教材とPortal共通文書は編集していません。

一次資料はNode v25のcoverage説明とStrykerのmutant states／metricsです。Strykerを実行した結果ではありません。コード・図・文章は独自制作、Apache-2.0。global install、公開、commit、pushは行っていません。

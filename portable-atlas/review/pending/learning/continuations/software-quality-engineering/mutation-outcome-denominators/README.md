# mutation reportの分母を読む

品質要求で検査対象を定める → 測定の分母と未知を確認 → 予算内のテストを選ぶ → 未実施・差なし・検出とmutation分母を解釈、という順序で読む小教材です。既存Software Quality LEARNING_PATHの次実験2を有限report集計として実装しました。元の「未実行」記述や原票は更新していません。

まずindex.htmlで8状態を各1件のreportを集計し、3つの分母を比べます。検出2件、valid 4件、covered 3件、total 8件。正しいmutation scoreは2/4=50%、covered版は2/3、全件数の確認用2/8=25%はStryker scoreではありません。故障checkboxを入れて再集計すると、未実行・無効をSurvivedへ混ぜたためvalidが8へ増え、scoreが25%になります。元のreportと正しい分類は残ります。

[Stryker公式](https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/)のMutant states / Metricsを参照しました。Timeoutはdetectedに含み、NoCoverageはundetectedですがcovered分母へ入れません。RuntimeError/CompileErrorはinvalid、Ignored/Pendingはscore分母の外にありtotalには含みます。分類理由を消してSurvivedへ付け替えません。Survivedの原因や同値性はこのreportだけでは分かりません。

これは**合成reportを実Pythonで集計する教材**です。Stryker、runner、自動mutation、実timeoutは未実行。statusは入力ラベルであり、実test結果の採取ではありません。完全なStryker JSON schemaのimportではなく、各rowがid/statusだけの平坦な独自契約です。ID m1～m8の最大8件・重複禁止・8status・fold exact boolを受理。unknown status、余分なkey、非文字列statusなどを拒否します。0分母は本教材ではundefined/null、表示%は6桁丸め、exact Fractionを保持します。

`python3 -B verify.py`と`python3 -B route.py`で、固定10report×故障有無の20例・18拒否・7集計mutantを照合します。受理可能な全report組合せの列挙ではありません。record/sealは制作時の一回だけで、通常再現で上書きしません。`python3 -B serve.py`が自身の127.0.0.1動的portを表示するので、そのindex.htmlで操作します。自身のserverだけをCtrl-Cで終了します。追加package不要。

画面のRequirements/QE/直前risk/既存Software Qualityリンクはallowlistされたread-only参照です。参照ファイルは本教材runtimeの依存ではありません。source viewerは32768文字を超える原票を明示的な抜粋と全文リンクで示し、保存JSONは完全です。browser証拠は実ツール観測の圧縮転記で、全文raw downloadとは呼びません。tool内captureが未保存なら画像path/hashを作りません。

本教材の問いは「何が分母に入り、次にどの理由へ戻るか」です。scoreの大小を製品品質・事故確率・coverageの十分性へ変換しません。全科目/Coreの完成は未評価。未教材はCOVERAGE.mdを参照してください。

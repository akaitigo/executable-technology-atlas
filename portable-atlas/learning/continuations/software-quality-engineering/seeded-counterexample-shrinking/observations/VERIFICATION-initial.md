# 検証の経路

実装前にhand-oracle.jsonへ24条件、6縮小trace、領域・seed・順位を固定しました。中央もproductionをimportせず集合と別計算で独立検算しました。これは実ブラウザ操作の代替ではありません。

CLI `verify.py --record attempt-01` は正常版/M1/M2×generator2×seed2×件数2の24条件、config拒否8、tuple schema拒否7、checker故障8、LCG全256cycleを実行して原票を保存します。通常verify/routeは原票の意味・digestを読むだけで保存記録を再生成しません。独立Oracleはproductionから期待値を受け取らず手表と集合による別表現へ照合します。

ブラウザでは同じ24条件を実UI/APIで実行し、生成全入力、候補全件、global失敗bit列、最初/最終/global反例を読みます。browser-cases.jsonはその実観測のcompact projectionであり、CLI原票のUTCをbrowserの時刻へ流用しません。予想全5値・全条件4種類の変更後、答え/生JSON/図/全tableの消去を確認します。保持した旧応答、schema拒否、source拒否と通信断も別状態として確認します。UIとQAの記録はui-qa.jsonに保存し、初回receiptを保持したまま一度sealします。

制作時、長いstdinによるUI authoringがUTF-8構文エラーで終了1となりました。ファイル書き込み前のparse failureです。authoring-attempt-01.jsonを保持し、file patchでUIを作成しました。失敗を正常実行に置き換えていません。ブラウザcaptureの画像がツールに表示されても、保存ファイルが得られなければsaved=false/path=null/hash=nullです。

最終のread-only-proof.jsonは通常verify/route/Skill validator/private-path検索の前後に全ファイルのSHA-256とmtime_nsを比較して最後に書きます。自分の専用listenerとタブだけを終了し、他教材・rootserver・protected portsへ操作しません。Core/global gate、公開、install、commit/pushは実行しません。

# keep-aliveの保持境界：対応範囲

状態：**固定2条件×4段階の実Widget観測成功、別Python191確認pass。保存実測readerのGUI/画像QA成功。別担当の最終受入は[現在の記録](ui-qa/reader-acceptance.json)を参照。**

ゴール45の「Stateの生成・保持・破棄を実Widgetと照合し、状態の所有階層と保存方法を選ぶ」に向け、画面外での保持要求を1つの有限な比較として扱います。

## 未対応境界を選んだ根拠

既存repoの`learning`、`labs`、`coverage.yaml`を`AutomaticKeepAliveClientMixin / wantKeepAlive / updateKeepAlive / keep-alive`で読取検索した範囲では、`learning/widget-state-lifecycle/README.md:107`の未教材列挙が見つかりました。Atlas全体に存在しないという判断には広げません。

直前の`flutter-listview-state`は並べ替えとcallbackを実測済みですが、keep-aliveを無効に固定し、有効時の比較を範囲外にしています。今回も12項目・固定viewportを使うものの、並べ替えを行わず、祖先wrapperは両条件で有効にして子の保持要求だけを変えます。前教材の原票・期待値・画像・受入文書は変更しません。

| 対象 | 今回の制作 | 状態 |
| --- | --- | --- |
| 祖先wrapperと子の要求を区別 | addAutomaticKeepAlives:trueを固定、wantKeepAliveのみtrue/false | 固定ソース照合 |
| 画面外の生成/保持/破棄を予想 | 2条件×4段階の手で固定した表 | 予測変更なしで実測と一致 |
| 表示中と生存中を区別 | 全Element/Stateと公開keptAlive/cache区分を記録するprobe | 要求ありのfar/returnedは生存4・cached2を観測 |
| 実務で保持と保存を区別 | 一時的な生存保持と外部モデル/永続化を分ける説明 | tree内の生存保持を確認。外部保存実装なし |
| 操作して予想と照合する | 保存実測readerの条件/予想・遠方/戻り・対照・原典・答え | 16確認・51実ポインター操作、1280/390pxの11実Chromium画像を目視確認 |
| 古い結果を残さない | 予想/条件/reset・取得失敗・digest不一致・旧遅延応答 | 行・対照・答え・ソースの消去を確認。native原票不変 |

動的`updateKeepAlive`の切替、reorder、Page/Tab、GlobalKey、外部モデル・process復元、可変高さ、性能・メモリー測定、FlutterライブGUI/pointer/drag・Flutter描画画像は別範囲です。reader操作は保存原票の選択・再生です。cachedのTextは生存Element読取で、paint証拠ではありません。固定ソースに`updateKeepAlive`の契約があることを説明しても、その経路を実測済みとは扱いません。

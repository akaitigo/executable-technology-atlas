# GlobalKeyの再配置：対応範囲

状態：3条件×4時点の実Widget検証、作者の別Python実装245確認、保存実測readerのGUI/画像QAが成功しました。別担当の最終受入は[現在の記録](ui-qa/reader-acceptance.json)を参照します。固定予測JSONは実行前の入力として不変です。

既存repoのlearning/labs/coverage.yaml/READMEを読取検索すると、`learning/widget-state-lifecycle/README.md:105`はGlobalKeyによる別位置への移動を未教材とし、`labs/framework-element-reconciliation/README.md:10`はreparenting costを別Proof Obligationとしています。検索範囲内の根拠であり、全Atlasに存在しないという主張ではありません。

| ゴール45との対応 | この単元の有限な範囲 | 受入条件 |
| --- | --- | --- |
| Widget/Element/StateとKeyの同一性 | 同型のAを別parentへ移す | 親は左右で異なり、GlobalKey同frameだけState/Elementを保持 |
| 入替・削除を予想し操作 | 同frame移動と一度除去を分ける | 3条件×4時点の原票と予測表を比較 |
| 生成・保持・破棄を照合 | initState/deactivate/activate/dispose | 原票イベントを独立したロジックで再構成、全State cleanup |
| 所有階層・保存を選ぶ | 子State内カウンター、外部保存なし | Keyによる生存の継続と永続化を混同しない |
| 操作し予想と照合する | 3条件の保存実測reader、12時点と2対照 | 17確認・60実操作、13実Chromium画像を目視確認 |
| 古い結果を残さない | 予想/条件/reset・503・digest不一致・旧遅延応答 | 古い行/対照/答え/ソースを消去し、後の結果を維持 |

上表のruntime受入条件は初回attemptで成立しました。同frameのGlobalKeyはS1/E2/1を保持し、除去後のGlobalKeyとValueKey対照はS2/E5/0を新規生成しました。親SlotのElementは全段階で不変、全Stateの終了時disposeも確認しました。readerの操作・画像は保存実測を読むブラウザーの検証であり、FlutterライブGUIではありません。

GlobalKey重複例外、型変更、InheritedWidget依存・費用、Route/Overlay、外部モデル・復元、FlutterライブGUI/pointer/drag・Flutter描画画像は未対応です。動的updateKeepAliveもこの単元へ追加しません。

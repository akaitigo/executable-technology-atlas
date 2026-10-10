# Atlas：言語の型とapplicationの方針

[Pythonの型一次資料](https://docs.python.org/3/library/stdtypes.html#boolean-type-bool)でboolがintの下位型であること、[JSON decoderの変換表](https://docs.python.org/3/library/json.html#json-to-py-table)で整数とtrue/falseの変換を確認しました。live資料は3.14系列、実機Python版は実行時に別記録します。今回のAPIはjson読取とexact typeの区別です。

`type(value) is int`でboolを除く、env booleanを小文字2語に絞る、十進regexと数値範囲は元subjectのapplication規約を再利用します。Python自体がこの設定schemaを決めるわけではありません。特に全層検証と勝者だけ検証、構造先検査、最初拒否、拒否nullは本教材の方針です。OpenFeatureの保証として説明しません。今回はSDK/providerを取得・呼出ししていません。

元subject evaluatorは全エラーを蓄積して最後に拒否します。ここでは最初の不正で止めるため、後続fieldを検査したと表示しません。既存ソースは必要範囲を読取っただけで、本文転載/全木copy/再実験は行いません。元資料のpath/hashと今回webのlocatorはrecords/reuse-and-sources.jsonへ固定します。

GUIでは公式リンクのexact URLへの実pointerとローカル遮断案内を確認しました。外部本文は取得・表示していません。制作時の一次資料読取と、資料HTMLの可視本文・Markdown downloadを区別します。詳しい範囲は[GUI_VERIFICATION](GUI_VERIFICATION.md)へ。

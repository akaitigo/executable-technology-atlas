# 二分探索：候補を失わず、範囲を縮める

Catalog ID `algorithms-data-structures` の有限な1教材です。[index.html](index.html)を開き、「予想→入力と操作→正常／異常比較→一次資料と実装→答え合わせ」の順に試します。重複と空列、未整列の前提違反も扱います。

通常のMac BrowserでHTMLを開ける構成です。今回の実画面QAは背景IABと専用localhostプレビューで実施し、file URLでの実行は未検証です。Node.jsが既にある場合は、このdirectoryで次を実行します。依存パッケージの追加はありません。

```sh
node serve.mjs
```

表示された127.0.0.1のURLを開きます。終了はCtrl+C。配信はこの教材の5ファイルだけで、他パスは404、外部接続は禁止です。別のターミナルで実装を確認する場合は：

```sh
node verify.mjs observations/my-new-run
```

新しい出力先を指定します。既存directoryを拒否し、runtime.jsonへ入力・状態列・結果・環境・時刻・Source digestを保存します。標準出力も同じ観測JSONです。Nodeで [search.js](search.js) を実行し、独立した線形走査の期待値と照合します。Browserの状態再生はこのJSの実行結果を図へ写す説明モデルであり、実行時間の測定ではありません。

## 分かること

反復で比較するindexは `[lo, hi)`、挿入位置pの候補は `lo ≤ p ≤ hi`。不変条件は左側の値が目標未満、右側が目標以上、境界が0〜nの順序を保つことです。範囲長の減少は停止のための別条件。検索する値がなくても挿入位置は求められ、一致は終了後に別確認します。

「候補を失う」で1,3,5から3を検索すると、正常はindex 1、hi = mid - 1の異常は見落とします。「縮まらない」の異常は長さ1の範囲を維持し、診断器で停止します。実際の無限ループを放置しません。未整列の3,1,2では正常は拒否、強行版は3を見落とし、線形探索はindex 0を返します。

16件・目標なしでは二分探索4比較、線形16比較。先頭一致では線形1比較、二分探索5回＋一致確認1回。整列済確認15回は別計上です。毎回前提確認する費用や診断の走査も含める場合、教材全体の実行量をO(log n)とは呼べません。実時間・メモリ・大量入力のベンチマークは未実施です。

## 記録と制限

[検証記録](VERIFICATION.md)に環境・生結果・画像・失敗と修正を記載します。[scope.json](scope.json)と画面の表にGraph、DP、tree、整列等の未教材領域を残しています。32要素以内・整数-999〜999・固定比較関数のモデルです。学習者の理解度・支援技術・多Browser・実端末は未評価です。

[この教材用Skill](skills/atlas-algorithms-data-structures/SKILL.md)は限定用途の再利用入口です。globalへのインストールや全Subject Skillの完成は行っていません。元Frontend repo、Portalのroot README／docs、Catalog、Core、Graph、Authorityには変更を加えていません。

一次資料は画面内からPythonのbisect仕様、CPython v3.14.0、Cornellの不変条件講義へ辿れます。説明・コード・図は独自制作、Apache-2.0。外部文書の参照は許諾素材やコード複製の証明とは扱いません。公開・commit・pushなしのローカル教材です。

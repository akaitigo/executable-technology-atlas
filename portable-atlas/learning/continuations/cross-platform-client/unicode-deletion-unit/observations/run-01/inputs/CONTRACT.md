# Atlas｜末尾の「1文字」を、どの単位で消す？

目標44の、正規化と編集単位の判断を扱います。既存JS/Pythonの単位契約とSwiftのCharacter/scalar/UTF16/UTF8計数・JSON往復を前提にします。今回は数え直しではなく、**正規化を先に一度行い、決めた末尾単位を一つ除いた結果**を比べます。

## アプリが選ぶ方針

この教材のアプリ方針は、末尾のextended grapheme cluster（拡張書記素クラスタ、以下EGC）を一つ除くことです。比較はUTF-16の末尾1コード単位、Unicode scalarの末尾1個、EGCの末尾1個の3方式です。scalar単位があらゆる編集で誤りだという主張ではありません。OSのBackspace/Delete、IME、caret、実端末UIの挙動は測りません。

正規化は `none`（変更しない）、`NFC`、`NFD` のいずれか。NFC/NFDの場合だけ対応APIを**削除前に1回**呼びます。削除後の再正規化や不正文字の補修は行いません。削除位置とsegmentのindexはすべて、正規化後の文字列のUTF-16コード単位offsetです。正規化前のoffsetを使い回しません。

空文字は受け入れ、3方式ともno-opとします。削除した単位数は0、cutOffset=0、残りも空です。空文字を「1件削除した」と数えません。非空は各方式の単位を1個だけ除きます。

## 入力と拒否順

要求は `text` と `normalization` の2keyだけを持つJSON objectです。以下の順に拒否します。

1. objectでない、array、null、未知key、key不足：`request-invalid`。
2. textがstringでない：`text-invalid`。
3. 入力textのUTF-16長が32を超える：`text-too-long`。
4. 孤立surrogateを含む：`unpaired-surrogate`。
5. normalizationがnone/NFC/NFD以外：`normalization-invalid`。

拒否は `accepted:false`、reason、`payload:null`。正規化・分割・削除の結果は返しません。入力を変更しません。固定拒否はnull要求、未知key、数値text、長さ33、孤立high surrogate、NFKCの6例で、全guardの全組合せや長さ32の端点を網羅しません。

## 先に固定する7要求

| 入力と処理 | 正規化後 | UTF-16削除後 | scalar削除後 | EGC削除後 |
|---|---|---|---|---|
| AB / none | AB | A | A | A |
| A e U+0301 / none | A e U+0301 | Ae | Ae | A |
| A e U+0301 / NFC | Aé | A | A | A |
| Aé / NFD | A e U+0301 | Ae | Ae | A |
| A😀 / none | 同じ | units 0041 D83D、不正scalar | A | A |
| A👩 U+200D 💻 / none | 同じ | units 0041 D83D DC69 200D D83D、不正scalar | A👩 U+200D | A |
| 空 / none | 空 | 空、no-op | 空、no-op | 空、no-op |

UTF-16方式が作った孤立surrogateは、コード単位列と `scalarValid:false` を保存し、scalars・UTF8・EGC分割をnullにします。U+FFFDへ置換して成功した測定のように見せません。JSON保存は孤立surrogateをescapeして保持します。画面でもescape/コード単位列を示し、壊れた文字を描画したglyphを正しい文字と呼びません。

正規化前・後のscalar/UTF16/UTF8、EGC列とUTF16 index、各方式のcutOffset、除いたUTF16列、削除単位数、残った列、有効性、今回のEGC方針との一致を保存します。NFCでこの結合例の結果が一致しても、NFCが分割APIの代用になったとはしません。

## 原典と独立確認

作者と独立担当はproducer前にliteralの符号位置・cluster列・削除結果を別々に固定します。producerは既存Node25.2.1の `String.normalize` / `Intl.Segmenter` を実行し、checkerはproducerをimportせず、固定literalと符号位置からの整数演算でUTF16/UTF8・切断位置を照合します。期待を実行結果へ合わせて書き換えません。

[UAX #29 rev43 / Unicode15.1](https://www.unicode.org/reports/tr29/tr29-43.html) の§3、GB9、GB11、GB999と、[UAX #15 rev58 / Unicode18.0](https://www.unicode.org/reports/tr15/tr15-58.html) の§1.2/§3を参照します。ECMA262/402は2025版のnormalize/Segmenterを参照します。資料版と実Node/ICU/Unicode版は分けて記録し、今回の古くからある固定文字・規則だけを照合します。Unicode全体の版互換を保証しません。

現時点は実装前です。対象実行は独立preexec確認、割当枠、直前資源確認後に、実nice10以上・子1個・wall15秒以内・retry0で行います。GUIは保存結果readerとして既存1pageで確認し、実計算/API実行と説明図を区別します。

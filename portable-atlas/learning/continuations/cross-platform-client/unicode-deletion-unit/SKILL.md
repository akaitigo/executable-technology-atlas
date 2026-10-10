---
name: atlas-client-unicode-deletion-unit
description: Atlasの保存結果で正規化時点と削除単位を分け、結合文字・孤立surrogate・書記素方針を判断する。
---

# Atlas｜削除単位の判断を案内するSkill

[読む順](README.md)→[学習画面](index.html)→[保存した結果](observations/run-01/results.json)→[原典](SOURCES.md)→[範囲](COVERAGE.md)へ案内します。結果が未作成/不一致なら、[実装前の期待](expected.json)を実測と呼びません。

保存結果はNode 25.2.1／ICU 78.1／Unicode 17.0による7要求・21結果と拒否6例です。以下では保存値を読み、実OSの編集を起動しません。GUIの確認状態は[別の記録](qa/reader-acceptance.json)で確かめます。

1. 「NFCにしておけば1文字削除は同じ？」：`combining-raw` と `combining-nfc`、`precomposed-nfd` の正規化後の列・切断位置・残った列を読む。NFC/NFDは表現の変換で、削除単位の代用ではないことを説明する。元の[Swift計数](related.html?topic=swift)を前提として再利用する。
2. 「emojiが壊れた。scalar単位ならEGCも守れる？」：`supplementary` と `zwj` の3方式を読む。不正UTF-16のunitsとUTF8=null、scalar-validだが今回のEGC方針には一致しない残りを分ける。補修やU+FFFDを本来の削除結果へ混ぜない。
3. 「実IMEのBackspace、全言語でも同じ？」：[契約](CONTRACT.md)と[未対応](COVERAGE.md)、UAX29の操作別tailoringへ案内する。これはアプリ独自の末尾操作と保存readerであり、OSキーボード・caret・native UIの実測ではない。空文字のno-opを削除1件として説明しない。

予想→保存結果→対照→原典/実装→答え→限界の順を保ちます。3例の読取利用は一般Agent評価や任意Unicode入力への正答保証ではありません。追加installや実端末操作をこのSkillで開始しません。

この3例は別担当が保存結果・前提・原典対応・範囲への導線を読んで確認しました。画面からSkill本文を開く実リンクも確認済みです。公式リンクのGUI確認は外部通信を遮断した遷移要求までで、本文は事前に確認した原典の版とlocatorを使います。

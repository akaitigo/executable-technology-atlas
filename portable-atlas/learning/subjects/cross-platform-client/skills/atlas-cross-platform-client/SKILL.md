---
name: atlas-cross-platform-client
description: Browser JavaScriptとPython stdlibの固定文字列契約を既存UI・runner・checkerで比較し、UTF-16単位数／コードポイント／UTF-8バイトの違いを学ぶ。native全OS保証やSubject全完成には使わない。
---

# 文字列の共有契約を比較する

このSkillからmodule rootは`../../`。READMEとscope.jsonを読んで、既存入力と実行対象を確認する。

「emojiでJS/Pythonの文字数制限が違う」は対応route。予想→UIの固定入力→JS実測と保存Python原票比較→validator.mjs・verify.py・oracle.json・原典→答えの順で案内する。4コードポイント、別の8 UTF-8バイト制限、未正規化、孤立surrogate拒否を変えない。表示文字数とコードポイントを同一視しない。

Python実行は`python3 -B verify.py`、保存済み原票の検証は`node check.mjs`。どちらも通常はread-only。記録更新だけ`--record observations/未使用名`を明示し、実Python・実Browserを再取得する。BrowserはREADME記載の最新原票を`node serve.mjs --python`へ渡してUIを使用。Source変更後は古い原票をdigest追記だけで通さない。自分のserver/tabのみ終了し、失敗原票を消さない。

「Android/Apple/Windowsでも動かして保証」「IME/アクセシビリティを全部保証」「本番の契約を勝手に変更」は未対応route。README/indexのE1–E4へ案内し、native実行未作成と必要環境を伝える。新依存・global install・Docker・外部サービス・権限・公開はこのSkillで許可しない。

正常routeは既存UIのemoji 2個を選び、keyboard Enterで実行。未対応routeはnative全OS保証の要求を拒否してE1へ案内する。同一Agentのroute確認は独立Forward Evalではない。

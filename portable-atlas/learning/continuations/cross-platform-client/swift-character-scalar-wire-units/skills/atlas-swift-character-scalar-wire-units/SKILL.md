---
name: atlas-swift-character-scalar-wire-units
description: 既存Swift CLIのJSON往復でCharacter/scalar/UTF16/UTF8とscalar/byte契約を実測する。iOSUI/IME/Kotlin/.NET/全graphemeには使わない。
---
元JS/Python→本README/固定codepoint/hex/count表→Swift実行→wire契約へ進む。正規化を挟まず配列/hexで再decode保持を確認する。String==だけではcanonical equivalenceを区別できない。
故障はscalar gateをCharacter countへ置換、UTF8 gateは維持。scalar超過かbyte超過かを別表示。UTF8 payloadとJSON全体のbyteを混同しない。
UIは各編集JSONを実Swiftへ送る。返った実resultから答えを生成し、全予想/input変更では旧本文/traceを空にしdetails閉、新値保持。revision違いの旧応答を破棄する。decode/host失敗に正常答えを出さない。
owned temporary compile/cache/binaryを除去。checker/runner通常はhash/mtime不変。明示--recordだけfresh immutable原票を書き旧raw保持。公開/install/全体gateに広げない。

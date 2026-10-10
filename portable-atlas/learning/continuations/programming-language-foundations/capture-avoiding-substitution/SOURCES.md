# 原典locatorと今回の独自拡張

2026-10-05公式Web参照。[Software Foundations / Programming Language Foundations / Stlc](https://softwarefoundations.cis.upenn.edu/plf-current/Stlc.html) のSubstitution、Technical note、closed termの説明。

同名binderで置換を止める例を確認する。Technical noteはopen replacementのfree nameがbinderへ捕獲される問題を説明し、closed termのstep relationではその複雑さを避ける。今回のopen-term捕獲回避は独自の小AST拡張で、原典コードを誤実装と呼ばない。

Int/Add、外側y=10、引数3、fresh v0/v1、AST validator、HTTP version検査は独自契約。Rocqを実行せず、STLCの型付け・progress/preservationを証明していない。本文/コード/図を転載せずlocatorを保持。

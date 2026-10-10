# Atlas：原典と実装の対応

[Software Foundations / Stlc](https://softwarefoundations.cis.upenn.edu/plf-current/Stlc.html) のValues、Contexts、Typing Relationを2026-10-06に公式本文で読取った。Fnは呼ぶ前から値として扱う一方、T_Absの型判断では拡張Γの下で本体を調べる。T_VarとT_AppはΓ参照と関数domainへの一致を支える。

原典のBoolと条件式をそのまま実装したものではなく、本教材はInt/Addを持つ小言語を定義する。Intと加算の規則、fail-fastな検査順、型注釈消去、入力制限、別診断経路は本契約の仕様。Rocqやprogress/preservationの証明は実行しない。plf-currentは可変URLであり、固定commitと呼ばない。本文大量copyはせず読取箇所と取得状態を [sources.json](sources.json) に保存する。

元入力と比較sourceの版・hash・場所もsources.jsonに固定する。source索引の存在を本文読了や全規則の実証と混同しない。

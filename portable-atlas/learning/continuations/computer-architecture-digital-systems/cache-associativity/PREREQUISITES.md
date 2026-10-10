# Atlas：blockからsetとwayへ

最初にbyte addressをline幅で割り、商がblock、余りがoffsetになることを確認します。元のdirect-mapped教材では、blockから1つのindexを決め、valid/tagを照合しました。その理解を使って「1つのsetの中に候補の置き場所が2つある」場合へ進みます。

読む順は、byteと商/余り → directのvalid/tag/fill → 同容量でのset数とway数 → hit時も更新するLRU → 返却byteと取得量 → 実務判断です。[契約](CONTRACT.md)と[手追跡](HAND_TRACE.md)を先に読み、保存結果がある場合だけ[画面](index.html)へ進みます。



今回必要なのは読出しの配置です。write policyやdirtyの知識を今回の実測として数えず、実CPUの速さを判断するときは構成・timing・workloadの別資料が必要です。

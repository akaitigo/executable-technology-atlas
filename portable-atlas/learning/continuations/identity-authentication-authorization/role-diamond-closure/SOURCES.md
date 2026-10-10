# Atlas：階層の語彙と教材の規約

[NISTの公開ページ](https://www.nist.gov/publications/nist-model-role-based-access-control-towards-unified-standard)から[著者論文](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=916402)を正式webで読み、§2.2 Hierarchical RBAC（PDFの3ページ目）を確認しました。senior roleがjunior roleの権限を得ること、hierarchyをpartial orderとして扱うことが語彙の根拠です。一般の部分順序と木だけに制限する構造は区別されています。

この教材の矢印方向、4role名、permission名、DFS順、active/visitedの実装、未知role拒否、null結果/例外形式は教材独自です。原典のpartial orderは反射性を含みますが、ここで入力するedgeは直接継承で自己edgeを列挙しません。開始roleをclosureへ入れることと、非自明なcycleを入力した評価拒否を分けます。NIST標準全適合を主張しません。

本文・図・コードの転載は保存しません。PDF全17ページの通読ではなく§2.2の小範囲読取で、原典はrecords/source-read.jsonにURL/locatorだけ固定します。GUIで公式リンクを押す確認は外部通信を遮断した案内とし、制作時の原典読取と混ぜません。

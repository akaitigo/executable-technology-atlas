# 学習順

1. writer×readerのcellを選び、受入か拒否を予測する。
2. writer-v1→reader-v2でnote列欠落の(default)を見る。
3. writer-v2→reader-v1で未知header拒否を確認する。
4. reorderedで正常名前mapとposition-faultを切り替え、parse成功のままquantityとunit_priceが入替わる理由を述べる。
5. empty-noteとmissing-note-cellを比較する。空文字、欠落columnのdefault、足りないcellの拒否は別である。
6. multiline-noteのphysical lineとdata recordの違いを読む。
7. 原典／反復producer／独立oracle／先に固定した手表へ進む。
8. 答えを開き、予測・typed行・拒否位置・receiptを照合する。

到達点：optionalという語だけで互換を決めず、名前と位置、型parseと意味、物理行とrecordを分ける。

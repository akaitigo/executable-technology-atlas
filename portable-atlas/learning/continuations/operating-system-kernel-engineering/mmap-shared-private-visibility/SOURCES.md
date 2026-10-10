# 原典・Darwin条件・取得attempt

- [Python 3.9 mmap](https://docs.python.org/3.9/library/mmap.html): 本文確認。ACCESS_READ/WRITE/COPYのassignment契約、Unix constructor/offset alignment、buffered fileのflush、mmap.flush、close節を照合。表示docs3.9.25と実行interpreter版はpatchが異なる。accessによる書込とflush/closeを別に扱う。
- [POSIX mmap Issue8 locator](https://pubs.opengroup.org/onlinepubs/9799919799/functions/mmap.html): 今回tool Internal Errorで本文未取得。[Issue7 locator](https://pubs.opengroup.org/onlinepubs/9699919799/functions/mmap.html)も403。POSIX本文確認済みとはせずlocatorを保持。一般POSIX/Linux全体の適合を今回のDarwin観測から主張しない。
- [Apple mmap(2) archive](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/mmap.2.html): 本文確認。MAP_PRIVATE/MAP_SHARED、offset page alignment、closeはunmapしないという契約を参照。古いarchiveで現行Darwinの全実装詳細を保証するものではない。

2026-10-05の取得attemptは上記成功/失敗を区別。第1単元の原典・raw状態は変更しない。第三者本文を複製しない。今回CPython/Darwin版、page_size、allocation_granularityは実[raw](evidence/current.json)から辿る。

**今回確認した事実**: 所有4byte file、同一process内の別read/mapping、actual assignment・flush・close・API例外。[実装](producer.py)、[独立literal期待](oracle.json)、[事前期待](EXPECTATIONS.md)。copy mappingのfile非変更は測定したが、何ページcopyされたかやpagefault/kernel内部の仕組みは測定していない。flush成功は電源断耐久性の実験結果ではない。

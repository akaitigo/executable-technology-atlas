# Atlas｜同じtarなのに、digestが変わる？

[学習画面](index.html)で、圧縮blobを指すdescriptorと、展開したtar全体を指すDiffIDを分けます。gzip headerのmtimeだけを変えた2つのblobを比べ、どちらのbyte列が変わったかを予想します。

1. [元OCI入口](related.html?topic=oci-base)の非圧縮tarとdescriptorから始める。
2. [有限契約](CONTRACT.md)を読み、同じtarに対するmtime0/1の違いと、指定条件の成功/拒否を予想する。
3. 保存結果を表示し、圧縮size/digest、gzip段階、非圧縮size/DiffIDを対照する。拒否の診断値は成功payloadとは別に読む。
4. [原典](SOURCES.md)と計算時の実装を確認し、答え合わせする。
5. 内容の一致と信頼、上限付き読取と一般の安全保証を分けて判断する。

画面は保存したPythonの計算を選んで表示するものです。操作でgzip処理やcontainerを実行しません。図は保存値を使った説明図で、実画面写真ではありません。

契約と期待を実装前に固定し、2026-10-06 18:17:41 UTC に Python 3.9.6 / zlib 1.2.12 で11条件を計算しました。正常2条件は、圧縮後がともに91 byteで異なるdigest、展開後が同じ2048 byteとDiffIDでした。残る9条件は、それぞれ指定した段階で拒否しました。

[実行ログ](verification/execution.json)では実優先度nice10、計算0.021221秒、計算と保存照合の逐次2子が計0.148623秒で終了しています。[作者照合](verification/saved-result-check.json)は308確認と6改変拒否、[独立照合の参照](qa/independent-cli-reference.json)は別に348関係と7改変拒否です。重複を含むため合算しません。独立側はproducerをimport・再実行せず、事前に別構成したtar全byteと保存結果を比較しました。gzipの別wrapper読取には共通のzlibを使う限界があります。

2026-10-06 19:01 UTCに共有headlessページで11条件の実DOMと代表3画像を確認しました。83回の実ポインター操作と、選択・移動APIの操作を区別しています。独立担当も表示と計算を207関係で照合し、3画像を目視しました。関連3資料はhrefから同じページへ移動して本文を照合済みですが、リンクの実クリックは未確認です。状態文の追補確認と最終独立受入は[確認状態](qa/reader-acceptance.json)へ。

元[学習経路66行](related.html?topic=learning-path)のgzip/DiffIDの不足に対応します。[opaque whiteout追加](related.html?topic=opaque)は別の受入済み概念で、再制作しません。旧repoへの統合・全OCI適合・runtime・registry・署名・host展開は対象外。[範囲](COVERAGE.md)、[手順](REPRODUCE.md)、[Skill](SKILL.md)へ。

# Atlas｜原典と今回の限定実装

2026-10-06に以下の公式本文を読取りました。第三者の本文・図・実装は転載しません。

- [OCI Image Spec v1.1.1 Layer / +gzip](https://github.com/opencontainers/image-spec/blob/v1.1.1/layer.md#gzip-media-types)とDistributable Format：gzip media typeはtar payloadをgzipで圧縮したもの。本教材は同じ2048byte tarを2つのmtimeで包む。
- [v1.1.1 Config / Layer DiffID](https://github.com/opencontainers/image-spec/blob/v1.1.1/config.md#layer-diffid)：DiffIDは非圧縮tar全体のdigest。本文fileだけのhashではなく、tar metadata/paddingも対象。compressed layer digestとは分ける。
- [v1.1.1 Descriptor / digest・size・Verification](https://github.com/opencontainers/image-spec/blob/v1.1.1/descriptor.md#verification)：参照するblobのbyte数とdigestを、処理に先立って確認する。期待値の信頼や署名をこの一致だけで証明しない。
- [RFC1952 §2.2 / §2.3.1](https://www.rfc-editor.org/rfc/rfc1952.html#section-2.2)：memberの連結、MTIME、CRC32、ISIZEを区別する。今回の連結拒否は単一memberという独自subsetで、gzip全仕様の無効ではない。
- [Python3.9 zlib / Decompress.decompress](https://docs.python.org/3.9/library/zlib.html#zlib.Decompress.decompress)：max_length・unconsumed_tail・unused_data・eofを使う読取。小さい入力とoutput capと有限回数を組み合わせる。一般的なarchive安全性の証明ではない。

[元OCI入口](related.html?topic=oci-base)は非圧縮tarの実生成と仮想map、[元学習経路](related.html?topic=learning-path)66行は今回の直接根拠。[opaque whiteout追加](related.html?topic=opaque)は圧縮tarを未検証と明記する。古い元READMEのopaque未対応を現在の分野全体の不足として数えない。

今回の正確な入力と拒否順は[CONTRACT](CONTRACT.md)、実装前の期待は[expected.json](expected.json)へ。gzip/digestを使うことをOCI全体・imageの安全性・署名認証・container起動の検証へ広げない。

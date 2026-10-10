# Atlas｜圧縮blobのdigestと展開後のDiffID

## 目標と前提
目標46・元OCI LEARNING_PATH.md66行の実験1に対応する。旧入口は非圧縮tarのdescriptor/DiffIDと小さいpath map、追加opaque whiteoutは下位/同層の適用を扱い、圧縮tarは未検証だった。今回補うのは「どのbyte列を識別するか」と展開上限であり、白印や仮想filesystemを作り直さない。旧repo/教材/共有計画は読取りだけ。担当者の現状は未確認、元repoへの統合はしない。

## 固定fixture
所有するmemory bytesだけで、単一のUSTAR通常file lesson.txt、内容ASCII `Atlas\n`（6bytes）、mode0644、uid/gid0、mtime0、uname/gname空、linkname空、devmajor/devminor0を作る。TarInfo.tobuf(USTAR_FORMAT)の512byte header＋本文とpadding512byte＋終端zero1024byteの計2048byte。tarfileの10240byte record paddingは付けない。hostへextractしない。
同じtarをgzip.GzipFile(filename='',compresslevel=6,mtime=0/1)で2回包む。gzip headerの4..7byteのmtime以外を一致させる。gzip mtimeとtar member mtimeは別。Python/zlibの版を実行記録に残し、別versionで同じ圧縮bytesになるとは保証しない。2blobの圧縮sizeは同じ、bytes/digestは異なり、展開2048byteとDiffIDは同じ、が実装前の期待。数値digestは実計算と独立照合で記録し、手で導出したhashと偽らない。

## 有限consumerと拒否順
入力は所有bytes、正確な3キーのdescriptor(mediaType,digest,size)、別に固定する期待DiffID、output cap。mediaTypeはapplication/vnd.oci.image.layer.v1.tar+gzip、digest/DiffIDは小文字sha256の64桁、sizeはboolでない非負整数、capは1..4096。入力blobは最大4096bytes。追加field/未対応形式は本教材のsubset拒否でありOCI全仕様の無効を意味しない。
入力形式/大きさ→descriptor size一致→圧縮bytesのSHA-256一致→上限付きgzip読取→単一memberの終了確認→展開tarのDiffID一致の順。拒否時は成功payloadなし、どの段階まで調べたかと部分的な診断値は別欄で保存する。digest一致は発行者の認証ではない。descriptorと期待DiffIDを攻撃者が共に変更できる状況の信頼は保証しない。
入力chunk64byte、decompress呼出し最大128回、outputはcap+1byteまでで打切り（上限を1byte越えた事実を検出するため）。eof前に入力が終わればgzip-incomplete。zlibの形式/CRC拒否はgzip-invalid。eof後の余りが1byteでもあればgzip-trailing-data。連結gzipもこの単一member subsetでは拒否するが、連結自体をgzip/OCI一般の不正と呼ばない。時間上限は外側15秒、無制限flushやhost展開なし。

## 11条件の手期待
normal-mtime0/normal-mtime1の2件は成功。同じgzipを「圧縮digest=期待DiffID」で直接比較するconflated-checkは故障対照で誤拒否し、正しい方式とは別に記録する。
wrong-sizeはmtime0のdescriptor.sizeだけlen(blob)+1へ変えてsize-mismatch。header-tamperはmtime0 blobのoffset4を0から1へ変更し（bytesはnormal-mtime1と同じ）、mtime0の古いdescriptorを保ってdigest-mismatch。changed-contentでは本文だけ `atlas\n`へ変えてgzipとdescriptorを作り直すが期待DiffIDは元tarのままなのでdiffid-mismatch。output-limitは元tarにcap2047を指定しoutput-limit。truncatedは末尾4byte欠落、bad-crcはgzip trailerのCRC最下位byteを1bit反転、trailingは元blob末尾にX、concatenatedは元blobを2回連結。これら4件は変更後blobにdescriptorを合わせ、gzip段階まで進める。順にgzip-incomplete/gzip-invalid/gzip-trailing-data/gzip-trailing-dataを期待する。
全条件は新しい独立memory状態で行う。一般の悪意あるarchiveや全資源攻撃の安全保証、tar適合検証、OCI layout全体の適合、zstd、署名、registry、container起動は範囲外。

## 原典と受入
OCI Image Spec v1.1.1 Layerの+gzipとDistributable Format、ConfigのLayer DiffID、Descriptorのdigest/size/Verificationを公式本文で実読。実装前に期待表を独立担当と固定する。保存blob/tar・header mtime・size/digest・各拒否段階・上限を照合し、改変や欠落の検出を確認する。readerは保存結果だけを読み、予想→操作対照→原典/実装→答え/限界の順。GUI経路は保留で実DOM/画像未実施、accepted:falseを維持する。SkillはmtimeとDiffID、自己整合descriptorの限界、上限/連結subsetの3例を資料で辿る。

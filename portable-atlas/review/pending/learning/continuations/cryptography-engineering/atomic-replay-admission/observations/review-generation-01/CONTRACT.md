# 認証済IDの確認と記憶

公開fixture鍵による実HMAC-SHA256照合を済ませた2要求A/Bを、同一プロセス内の有限集合seenで受入判断する。認証失敗は集合を読まず、書かず、受け入れない。IDはASCII英大文字・数字・`_-`の1〜16文字、payloadはUTF-8で0〜64 bytes、tagは小文字hex64文字。入力はexactキーで、seenは同じID規則の重複なし最大16件。鍵は教材専用の公開値で秘密ではない。認証bytesはID、NUL、payloadの順。形式違反は実行前にValueError。

split: check時の未登録判定を要求ごとに保存し、その値をwrite時に使う。writeで再確認しないので、集合自体は重複を持たなくても受入が重複する。atomic: checkと条件付きremember/acceptを1イベントにまとめる。MAC確認はどちらもstate操作より前。

## 先に固定した手表

同じ未登録ID、両要求が認証成功した場合。c=check、w=remember/accept。

| schedule | 順序 | 受入数 |
|---|---|---:|
| split-1 | Ac Aw Bc Bw | 1 |
| split-2 | Ac Bc Aw Bw | 2 |
| split-3 | Ac Bc Bw Aw | 2 |
| split-4 | Bc Ac Aw Bw | 2 |
| split-5 | Bc Ac Bw Aw | 2 |
| split-6 | Bc Bw Ac Aw | 1 |
| atomic-AB | A B | 1 |
| atomic-BA | B A | 1 |

異なる未登録IDは全8順序で2。事前登録済の同一IDは0。両方invalid MACは0でseen不変。Aがinvalid/Bがvalidで同じ未登録IDは1。同じIDで異なる認証済payloadもID単位の上記手表に従う。16文字ID・64bytes payloadでも同じ。同じIDの逐次要求はsplit-1/6が代表する。

traceは初期状態と各イベントの直後を含む。要求ごとのauthenticated、cached_absent（未checkはnull）、status、累積受入数、seenを出す。認証失敗のcached_absentは常にnull。既存集合を変更するのは認証成功かつ受入時だけ。

## 実threadの証拠範囲

有限schedulerの全6順序と実thread代表観測を分ける。splitはcheck後の2者Barrierで同時に未登録を確認した代表例を強制する。atomicはLockの前でBarrierを待ち、Lock内でcheck+rememberを行う。Lock内部にBarrierを置かない。sleepによる順序制御をしない。Barrier/Lockはtimeout、joinは期限付き、失敗時はabortと再joinを行い、生存threadと例外を記録する。失敗を成功に数えない。意図的なbroken Barrierも失敗観測として残す。

DB、永続化、TTL、再起動、分散処理、ESP実装、配送や副作用のexactly-once保証は対象外。RFC4303 §3.4.3–4は認証成功前にanti-replay状態を更新しない根拠として参照するが、そのsliding windowを本集合モデルへ実装したとは主張しない。

# 一致したrootを、誰から受け取ったか

[元Subjectのcoverage第3候補](../../../subjects/decentralized-systems-blockchain/README.md)から独立した有限Merkle教材です。架空bytes4葉、実hashlib SHA256、depth2の位置つきmembershipを比較します。**検証者が独立に保持するtrusted rootは事前固定fixtureの仮定**です。root配布・認証を実装したものではありません。中央受入待ち、Subject全体の完成ではありません。

## 固定契約と事前手表

葉順はhex 41,42,41,44（A/B/A/D）。Aを位置0と2に重複させます。位置つきmembershipが通っても値が一意とは言えず、人物・由来の証明にはなりません。index0..3のbit0/bit1が各levelの左右を決め、proofはleafからrootへ2兄弟。兄弟sideはindexと一致しなければ形式拒否。

leaf=SHA256(0x00 || decoded bytes)、internal=SHA256(0x01 || raw left32 || raw right32)。空leafは許可。leafはlowercase even hex0..16bytes。**兄弟hashとsender_rootは64文字の小文字hexを32raw bytesへdecode**します。hex文字自体をhashしたり、左右をsortしたりしません。double SHA、padding、treeの奇数葉処理はありません。教材独自のencoding/domain separationで、NISTのwire protocol規定やRFC8785準拠ではありません。

[契約](contracts.json)、[事前手表](hand-oracle.json)、[producer前hash](qa/oracle-before-producer.json)を先に固定。SHA演算は手計算していません。事前fixtureは独立full-tree経路で生成し、[checker](checker.py)は全葉から再構築する経路とindex別に2段を明示する式でpath foldを照合します。primitiveはhashlibを共有するため完全に別の暗号実装とは呼びません。NIST公開abc固定vector・empty vectorとsystem OpenSSLの別backendでも照合します。FIPS認証ではありません。

| 条件 | 同送root一致 | 固定trusted root一致 | 意味 |
|---|---|---|---|
| 正常4位置 | true | true | そのrootに対する位置つきmembership |
| leaf改変／兄弟hash順逆 | false | false | fold不一致 |
| 同送rootだけ違う | false | true | membershipは固定rootで判定 |
| leaf0変更＋木/proof/同送rootを再計算 | true | false | 内部整合は信頼の根拠にならない |
| 兄弟欠落/余剰、side違い、hex不正等 | 形式拒否 | 判定なし | depth/index/byte契約外 |

trusted rootはcalculate.pyの検証者所有literal。requestにtrusted_rootを追加するとshape拒否します。receiverはleaf/index/2兄弟/sender rootだけを受け取り、baseline全葉を読みません。同送rootは診断用で正しいtrust anchorに昇格させません。「再計算」例はleaf0のAをZへ変更し他3葉を維持した木全体の再計算で、全leafを変更する例ではありません。

## 予想 → 操作 → 比較 → 原典/実装 → 答え

このディレクトリで python3 -B checker.py、python3 -B runner.py、python3 -B server.py を実行します。固定原票の新UTC保存は明示操作 python3 -B runner.py --record だけです。

serverが印字するtask-owned loopback URLで画面を開きます。予想を選び実JSONを送信。leaf/2兄弟のhash図、左右/preimageを含むtrace、derived/sender/trustedの3rootと採否を比較します。「leaf0変更・同送tree再計算」1操作は例を実childへ送り固定trusted rootを保持します。原票/実装は固定allowlist text viewer。JSON・予想・例・reset変更で旧図/表/原票/答えを消しdetailsを閉じます。遅延した旧結果は復活させません。

通常runner/checkerとserverのGET/POST/exportはunit SHA/mtime不変。原票はRAM最大512件で停止時に失効し、新serverは新原票。QAの明示採取だけ専有dirへ保存します。14mutantは同送root採用・request anchor・domain tag・hex文字hash・左右/順・省略/重複・index無視・一意/内容真/署名/合意/配布認証の偽称を検出します。

## 原典・限界

[NISTIR8202 §3.6 pp15–16 / Appendix B p53](https://nvlpubs.nist.gov/nistpubs/ir/2018/NIST.IR.8202.pdf)はblock rootとMerkle treeの概念の根拠。[FIPS180-4 §6.2 pp21–23](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf)はSHA256仕様。[NIST abc example](https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Standards-and-Guidelines/documents/examples/SHA256.pdf)は既知digestの確認。これらが本教材のdomain tag/byte形式/root信頼配布を規定したとは扱いません。

membershipは内容の正当性・署名/認可・consensus・fork/finality・履歴の唯一性を保証しません。hash collisionが不可能と証明したものでもありません。live chain・実資産・外部dataset・wallet・署名鍵・network/速度bench・汎用Merkle/軽量client protocol・root配布の信頼性は未実装。[COVERAGE](COVERAGE.md)/[sources](sources.json)/[Skill](skills/atlas-merkle-membership-trusted-root/SKILL.md)/[QA](qa/README.md)。

global/index/manifest・旧教材は変更せず、保護資源に触れません。install/fullGate/commit/push/公開なし。repo全体verifyは依頼の範囲外で未実行、局所結果をrepo全体成功に読み替えません。

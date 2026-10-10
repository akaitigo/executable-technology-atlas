---
name: atlas-huffman-payload-header-cost
description: 合成ABCDのHuffman平均長と実payload/header費用を、この有限教材と原票で学ぶ。標準codec性能やcapacity保証の依頼には使わない。
---

# 有限Huffman教材

このSkillは教材内の候補で、global Skill導入/登録ではない。README、contracts、handを読み、実装前手表→独立checker→実入力比較→答え→MIT原典の順で進める。

1. skew-shortでheader込み判定を予想し、JSONを実行する。14対16payloadと30対24totalを説明する。
2. messageを5倍にする1操作で同modelのまま40記号86対88を比較する。×4の72対72も比較する。
3. uniform、CDCD mismatch、空を比較し、L/Hと有限messageの実平均を分ける。空の実平均は未定義。
4. 実codebookとmerge履歴、header長、receiverのcodebook/bitstream/countのみの入力を原票で読む。原messageはharness専用。
5. producerをimportしないcheckerのprefix・別復号・Kraft13割当・平均長と費用のoracleを確認する。

通常checker/runner/routeは`python3 -B`でreadonly。明示recordだけ新UTC排他保存・固定pointer更新し、既存rawは上書きしない。serverはown loopback memory-only、owned server/tabだけ停止/closeする。予想/JSON/scenario/reset後は図・答え・rawをclearし、旧応答の再表示を拒否する。

alphabetはABCD共有、positive weight1..16、message0..255、Huffman16bit/fixed8bit headerの独自bit規約。未知記号・未対応format等は正規化せず拒否。未対応依頼はCOVERAGEの入口へ案内し、分野complete・標準適合・速度・capacity達成・物理通信・認証を主張しない。

# Atlas KR-03 の対応範囲

Kotlin の分野目標 23 にある JVM の基礎・固定期待値による比較を前提とし、KR-02 が準備した `comparisons.behavior-variants` / `stdlib.delegates` の mode 比較へ進む課題です。目標文書の次課題そのものを mode 比較へ書き換えたわけではありません。元 gap `authority.exhaustive-locator-review` を、この局所検証だけで閉じません。[KR-02 の概念と残る範囲](../kotlin-delegation-concept-map/COVERAGE.md)、[KR-01 の有限 Router](../kotlin-router-scope-repair/README.md)は読取り専用です。HTTP からは[前提一覧](references.html)を使えます。

**五条件の初回実測と保存結果の125照合・6改変拒否まで完了しました。** 旧load判定による未起動版を保持し、その後のload5.9004の専有枠でcompile1/JVM1、retry0で実行しました。画面・画像・独立受入の状態は [status](status.json) を参照してください。測定だけでそれらを完了扱いしません。

| 問い | 固定条件・根拠 | 境界 |
|---|---|---|
| 逐次読取りで計算を保持するか | 三 mode 各 2 回の読取り | 成功する initializer だけ |
| 二者が読むと計算回数はどうなるか | SYNCHRONIZED と PUBLICATION、最大 2 worker | PUBLICATION 1 回も受理。分布・性能は扱わない |
| 計算した値と公開値は同じ問いか | count と id / marker と `===` を別に保存 | id だけを参照同一性の証明にしない |
| 終了後 main は何を読むか | 両 Future の完了後に再読取り | 実装した共通期限と有限回収に限定 |
| 不成立・途中失敗を残せるか | priority の実値、exec 到達、部分 stdout/stderr、回収状態 | 模擬した拒否は実 Kotlin 失敗とは別 |
| 視覚的に確認できるか | 保存結果の再生・概念図・比較表 | 実画面の確認状況は status を参照 |
| 通常の案内で使えるか | 限定 Skill と参照の入口 | 文書の存在と Agent の実利用評価は別 |

NONE の並行、例外後再試行、再入、一般 property/class delegation、全 JVM/他 platform、性能は未検証です。旧 LazyProbe の 0→1 / 2 read / once は既存の逐次成功証拠であり、新しい実験件数に再加算しません。専用 proof 10 件全体の完成を主張しません。

KR-03 の五条件の実施状態、画像の確認、独立受入は [status.json](status.json) を正本の案内にします。元 repo 統合、正式な人の意味分類、全体の集計はこの作者の範囲外です。次の問いは「initializer が例外を投げた後、次のアクセスで何を再試行するか」ですが、この教材の制作中に新しい実験を連鎖して開始しません。

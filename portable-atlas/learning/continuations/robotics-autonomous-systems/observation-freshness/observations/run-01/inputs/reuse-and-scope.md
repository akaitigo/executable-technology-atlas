# Atlas — 既存186からの次の問い



| 既にある教材 | 再利用する判断 | 今回との違い |
|---|---|---|
| [点grid](related.html?doc=base) | mapは知識、worldと一致するとは限らない。次edgeを再検査 | robot.pyのafter_moves一回追加は時刻付きの逆順/期限検査をしない |
| [footprint](related.html?doc=footprint) | 幅・閉領域・接触を幾何で判断 | 今回は既に固定された次edgeの対象cellだけを読む |
| [制動距離](related.html?doc=braking) | 遅延と速度/減速度で止まれる距離を分ける | 今回のageは知識の期限であり制動時間ではない |

新しい判断は、届いた順に採用してよいか、古い観測を拒否した後に何を保持するか、期限超過やunknownをfreeと区別できるかです。[契約](CONTRACT.md)→[保存reader](index.html)→[Skill](SKILL.md)を接続します。探索、幾何、制動を重複実装せず、作者の全体加算は0です。

共有ownerへの正式接続が得られていないことを、owner不在や置換許可とは扱いません。共有repo・先行186・台帳は変更しません。

# Atlas — 前提から今回の問いへ



| 前提 | 既に扱う判断 | 今回加える問い |
|---|---|---|
| [counter](related.html?doc=counter) | clock edgeで全registerを旧値から更新 | 別周期・位相のedgeが同じ信号をどうsampleするか |
| [ready-valid](related.html?doc=ready-valid) | stall中に値を保持、同一edgeで捕捉後に更新 | 短い事象をそのまま別clockへ渡すと見えない場合 |
| [元の範囲](related.html?doc=coverage)の次3 | pulse/level/toggleと失う事象が次課題 | 5固定例のsample、2FF、検出時刻と未観測件数 |

元counterの理想同時更新とready-validの保持を再び新原理として数えません。今回の増分は、送信側で起きた事象と宛先でsampleされたlevelを分けることです。教学側は送信事象を知りますが、宛先の論理は見えなかった事象数を知りません。

[契約](CONTRACT.md)→[画面](index.html)→[限定Skill](SKILL.md)へ進みます。正しいHDL記述、合成、物理CDC解析、製品macro、ack/FIFOへは範囲を広げません。作者による全体件数の加算は0です。

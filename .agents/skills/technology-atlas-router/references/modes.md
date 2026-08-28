# Modeと返却契約

| Mode | 使用する問い | 必須返却 |
|---|---|---|
| `discover` | 分野や技術を探す | Subject候補、Catalog状態、固定Releaseの有無 |
| `compare` | 近接分野を区別する | 各SubjectのScopeとExclusion、判断根拠 |
| `verify` | 完成・署名・Digestを確認する | Release URI、Digest、署名鍵、Certificate、検証状態 |
| `evidence` | Claimの証拠を探す | Target state、Evidence ID、verdict、環境、3 Digest |
| `skill` | Agent用Routerを探す | Router ID、固定Atlas Release、Adapter、Eval閾値 |
| `gap` | Coverage外や未完成を確認する | 欠落状態、理由、同等ではない代替候補 |

どのModeでも、`app/data/index.generated.json`の`digest`を返却の根拠にする。候補が複数ならScopeとExclusionで絞り、推測で1件に固定しない。

---
name: atlas-contract-evolution-invalidation
description: 合成JSONの有限品質contractでmax/version/表記変更のcache失効と再検査を比較する。CSVW準拠・実データ承認・cache真正性保証には使わない。
---
READMEとcontracts.jsonを読み、route.pyの6入口へ依頼を対応づけ、UIの予想→binding→再評価/違反/合計→答えを辿る。
失効、再評価受理、再評価拒否を別stateにする。versionはcache identityに含まれるmetadataで、validation predicateを変えない独自契約。空白/key順は正規化後のidentityを変えない。
checker.pyは手書き表・固定byte/hash・独立sumのread-only検算。通常runnerは書かず、再記録の明示依頼だけrunner.py --record。
source-only故障cacheは契約hashを無視し、max99でも旧合計100を返す。hash一致/不一致から意味的正しさ、承認、真正性を推定しない。
CSVW適合認定、実データ承認、cache真正性、全schema migrationは未対応としてREADME次coverageへ。実service・新権限・公開・課金をこのSkillから推定しない。

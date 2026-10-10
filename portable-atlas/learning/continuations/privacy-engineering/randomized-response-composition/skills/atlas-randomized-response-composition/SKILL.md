---
name: atlas-randomized-response-composition
description: 合成1bit randomized responseの全coin経路を有限計算し、1回答と独立2回答の比3/9、composition故障対照を検算する。実人物・一般DB・サービスprivacy保証には使わない。
---
READMEとcontracts.jsonを読み、route.pyの6入口へ依頼を対応づける。UIで予想→保存分布・両方向event ratio→故障判定→答えを比較する。
隣接は単一合成bit0↔1。2回答は同じbitへの独立coinを使うjoint。既存12件tableのDP化ではない。random samplesは0で、全分布をFractionで厳密計算する。
ratio3/9はepsilonそのものではない。delta0でexp(epsilon)のboundとしてln3/2ln3へ接続する。marginalだけを見たbound3流用はjoint00/11で破れる。
checker.pyは手書き表＋独立Fraction直積の読み取り検算。通常runnerは書かず、再記録の明示依頼だけrunner.py --recordを使う。
既存table DP化、実人物再識別、一般DB accountant、実サービス安全保証は未対応。README次coverageへ案内し、実データ・外部service・新権限・公開・課金をこのSkillから推定しない。

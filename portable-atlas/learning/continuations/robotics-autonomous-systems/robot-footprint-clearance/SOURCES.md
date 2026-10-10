# 原典と今回の数学model

- [LaValle, Planning Algorithms, Ch4 §4.3](https://lavalle.pl/planning/ch4.pdf): PDF本文取得。§4.3.1、印刷pp.157–158（PDF pp.16–17）のC-space obstacle定義、§4.3.2、式4.37–4.38、印刷pp.158–159（PDF pp.17–18）のMinkowski差/和を確認。円は対称なので今回Cobs=O⊕disk(r)。今回のstrip/corner実装と閉集合接触のfixtureは作者の構成で、図や本文を複製しない。
- [Nav2 Jazzy Environmental Representation](https://docs.nav2.org/jazzy/getting_started/navigation_concepts/environmental_representation/): 既存costmap locatorを今回取得、environmental representation/costmapの本文確認。今回Nav2/ROSは実行せず、自作のexact binary geometryを扱う。
- [Nav2 Jazzy Inflation Layer Parameters](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/costmap_2d/costmap_plugins/inflation/): 本文確認。Introduction、inflation_radius、cost_scaling_factor。公式pluginのcost decay/inscribed radiusと、今回の円footprintによるbinary C-space regionを同じ実装や同じparameterだとは扱わない。

取得attempt（2026-10-05）: 最初の現行short locator `https://docs.nav2.org/configuration/packages/costmap-2d.html` と `https://docs.nav2.org/configuration/packages/costmap-plugins/inflation.html` はtool Internal Error。上の既存Jazzy locator本文取得へ切替。失敗を成功扱いしない。原単元の資料/原票状態は変更しない。

数学契約・独立期待は[EXPECTATIONS](EXPECTATIONS.md)。producerは膨張したregionとのsegment交差、oracleは元障害物への最小距離をFractionで比較。入力は固定[fixture](fixture.json)だけ。図はcode-native SVGで、実robotの写真・sensor画面ではない。IAB captureはそのSVG教材を実際に操作したbrowser画面。

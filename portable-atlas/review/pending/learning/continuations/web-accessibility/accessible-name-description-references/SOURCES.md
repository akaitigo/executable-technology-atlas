# 原典と版

2026-10-06 JSTに[AccName 1.2 2026-10-02 Working Draft](https://www.w3.org/TR/2026/WD-accname-1.2-20261002/)の版と本文を確認。Recommendationではなく更新可能なdraft。本文/code例を複製せず独自fixtureを使用。

- §4.2 Description Computation: describedbyによる補足はnameと別の値。説明の優先順位と、最初に適用できる候補の扱いを読む。
- §4.3.2 Hidden Not Referenced: hiddenを一律除外しない。直接参照したhiddenのsubtreeと、可視参照先のhidden子を区別。
- §4.3.2 LabelledBy / AriaLabel / Name From Content: 有効な参照、IDREF順、aria-label、native button内容の順を、この有限fixtureの条件で比較。

[Portal学習経路](../../../subjects/web-accessibility/LEARNING_PATH.md)は読み取り参照。既存QEにも新READMEからのみ接続。仕様期待・IAB name観測・description未観測・実AT未実施を混ぜない。

# 元学習経路からの増分

元distributed-systems/LEARNING_PATH.md §6実験2のcomplete register historyを実checkerへ進めた。初期0、最大4操作、precedence DAG探索と独立全permutation spec、完了後stale read、重なるread0/read1、response-sort反例、2write/2readを扱う。

schema-valid8historyは合法6・非合法2。契約外6fixtureは入力拒否として別枠。元max-registerの収束原票は流用/変更しない。合成historyは実DB/network計測ではない。pending等の未網羅と次3案はREADME参照。

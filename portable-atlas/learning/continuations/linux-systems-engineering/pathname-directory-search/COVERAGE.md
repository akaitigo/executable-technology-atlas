# 元coverage → 今回 → 残範囲

[元Subject](../../../subjects/linux-systems-engineering/README.md)のstorage/security（README:77）を参照。今回だけ合成/vault/reportで各directory search、末端read、unknown/non-directory、first stopを有限実証します。

| 残る問い | 次の有限実験案（未実行） | 原典locator |
|---|---|---|
| ACL/capability/LSMが通常9bitとどう重なるか | 明示した追加policy層と独立oracle | [path_resolution Permissions/Bypassing](https://man7.org/linux/man-pages/man7/path_resolution.7.html) |
| mount/namespaceでrootと見えるinodeが変わるか | 合成namespace→root table、対応Linux隔離実験 | [Step 1/Mount points](https://man7.org/linux/man-pages/man7/path_resolution.7.html) |
| symlinkやrelative pathはどの順に解決するか | 有限link chainと停止limitを別契約で比較 | [Step 2/. and ..](https://man7.org/linux/man-pages/man7/path_resolution.7.html) |
| 実kernel/FS取得と合成模型は一致するか | Linux隔離runtime・非特権test treeでread/searchを追試 | [Step 3/Permissions](https://man7.org/linux/man-pages/man7/path_resolution.7.html) |

Mac chmodをLinux適合証拠にしない。Security object認可への関連は存在と取得の境界という観点だけでpolicyを同一視しない。

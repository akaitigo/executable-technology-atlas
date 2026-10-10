# Skillローカルrouting review

2026-10-05、Codex自己レビュー。独立Agent Forward Evalではない。

## 正常依頼

「1bit・dataを反転するとどこを直すか」という依頼をSkillの既存runnerへRouteした。

```sh
/usr/bin/python3 -B lesson.py --case single-data
```

実行応答時刻は`2026-10-05T05:15:49.773861+00:00`。exit 0。入力`1011`、誤り位置6、送信`0110011`、受信`0110001`、syndrome 6、decoder反転6、復号`1011`、post-syndrome 0、ground truth一致。G/Hと最短符号語oracleも一致。これらは[全単一bit保存観測](python.json)と同じ結果で、source digestも一致する。説明だけを実行Proofにしない。

## 対応範囲外依頼

「SECDEDで2bitを検出して」という依頼は、この教材の[範囲表](../README.md#対象範囲)へRouteする。SECDEDは未実装と回答し、7bitの誤訂正反例をSECDED検証済みとは扱わない。

CLIの未対応modeもfail-closedか、実際に確認した。

```sh
/usr/bin/python3 -B lesson.py --case secded
```

exit 2、stderr:

```text
usage: lesson.py [-h] [--record]
                 [--case {no-error,single-data,single-parity,double-counterexample}]
                 [--port PORT]
lesson.py: error: argument --case: invalid choice: 'secded' (choose from 'no-error', 'single-data', 'single-parity', 'double-counterexample')
```

未対応modeを既存caseへ置換せず、Artifact作成や別Repository操作は行わなかった。

## 検査と制約

`quick_validate.py skills/atlas-information-theory-coding`は`Skill is valid!`。descriptionはHamming(7,4)の有限教材に限定し、SECDEDや別符号の未実装を明記。commandと相対リンクは実在する。記録書込みは明示flagのみ。常駐Skillのglobal installはしていない。self-reviewの結果は独立モデルrouting能力の測定ではない。

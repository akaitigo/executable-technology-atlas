---
name: atlas-cache-associativity
description: 同容量のdirect/2-way cacheの保存traceから、配置・LRU・byteの正しさと比較条件を判断する。
---

# Atlas：配置と置換の保存証拠を読む

通常は[status](status.json) → [前提](PREREQUISITES.md) → [README](README.md) → [保存計算](MEASUREMENTS.md) → [画面](index.html) → [原典・実装](reference.html)へ進む。未実行なら[手表](HAND_TRACE.md)と[契約](CONTRACT.md)だけで説明し、予想を実測と言わない。GUI保留なら本文/保存JSONを読み、browser/serverを起動しない。証拠を読むための模型再実行は不要。

次の6問だけを、入力→該当read→前後state→原典/実装→限界へ結ぶ。

1. 同じ16B/line4Bなのにset数が4から2へ変わるのはなぜか。wayと容量の増加を混ぜない。
2. 0/16の再訪が2-wayでhitになる理由をvalid/tagと実wayで説明できるか。
3. way数を超える同setの3blockで、2-wayがdirectよりmissを増やすことがあるか。選んだtraceだけの反例と一般優位性を分ける。
4. hit-recencyの3回目でLRU→MRUがどう変わり、4回目のvictimへどう響くか。故障版でもbyteは正しいことと別に答える。
5. address255と252は同じblockか。要求1byte・取得4byte・offset・tagを区別し、空traceのhit率nullを0と呼ばない。
6. 取得失敗、入力拒否、模型実行失敗、正常終了した故障比較は何が違うか。wall timeを実CPU cache性能に転用しない。

固定5trace/11結果以外の一般LRU定理、任意geometry、write/dirty、coherence、実CPU性能、学習者/一般Agentの能力は確認外。新実行は独立review・root fresh/単独枠・nice/deadline/回収を別に確認してから行い、古い資源許可を使わない。

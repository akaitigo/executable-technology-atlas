---
name: template-edit-preservation
description: 専用tmpのflat JSON descriptorでtemplate更新の手編集保持と衝突時apply書込0を検証する。Backstage標準mergeや既存project更新には使わない。
---

README→手表→runner→独立byte oracleを読む。python3 -B verify.py / route.py は実tmp再計算と保存artifact再readを行うがmoduleに保存しない。明示recordは未使用attemptだけ、sealはQA後だけ。UIで予想→実write/read→正常/故障→原典/source/raw→actual答えを確認し、全予想変更/local/pathreset、拒否と実失敗と旧応答を区別する。一般text/rename/delete/multifileatomic/Backstage実運用は未対応と明記。既存project、global installには進めない。

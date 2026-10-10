# 実tarと独立照合

事前手表を固定し、13条件で実USTARを生成・tarfile読取・map適用。各tar digest/size、member名/type/size/exactbody/linkname、入力lower前後、finalmap、UTC/runtime、実ReadErrorを原票に記録する。保存tar26個を独立manual header decoderで再readし、literal最終map・拒否表と照合。6改変を拒否。通常checker/routeは専用tmpだけで再生成し、全module file sha256/mtime不変をproofへ最後に保存。

実IABで13条件、全予想4値の開答えからの単独変更、scenario/payload/markerreset、可変payloadのactual答え、拒否/実失敗で正常答え解除、旧応答非採用、5source導線を確認。captureは実tool画像、保存不可ならsaved=false/path/hash=null。所有server/tab/tmpのみ終了。有限Skillの検査は独立Agentや利用者理解度の測定ではない。

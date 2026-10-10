# 増分と境界

元tiny bytes模型のundeclared inputを、実Apple clangのCPATH header探索と実native binaryへ進めた。source/compiler/flag-only bad keyのstale hit、同B入力clean build、実解決header bytesを含めたgood keyのmissを5attemptで比較した。

扱う依存はowned banner.hだけ。SDK/linker/全toolchain/全envをpinしたhermetic buildではない。別compileの同stdoutでもnative digestが違ったことは観測したが原因切り分けは未実施。元Subject原票・coverageはread-only保持。次の3具体実験案はREADMEにあり未実行。

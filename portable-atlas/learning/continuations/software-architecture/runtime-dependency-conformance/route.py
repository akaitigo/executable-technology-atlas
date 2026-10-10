import sys,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent
if sys.argv[1:]==['inspect']:sys.exit(subprocess.run([sys.executable,'-B',str(R/'checker.py')]).returncode)
elif sys.argv[1:]==['lesson']:print('index.html; evidence '+(R/'CURRENT').read_text().strip())
elif sys.argv[1:]==['record']:sys.exit(subprocess.run([sys.executable,'-B',str(R/'runner.py'),'--record']).returncode)
else:print('unsupported route',file=sys.stderr);sys.exit(2)

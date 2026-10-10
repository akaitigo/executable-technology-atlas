import os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OPENSSL=Path('/opt/homebrew/opt/openssl@3/bin/openssl')
VERSION='OpenSSL 3.6.3 9 Jun 2026 (Library: OpenSSL 3.6.3 9 Jun 2026)'
def command(args):
    if not OPENSSL.is_file():raise RuntimeError('required existing OpenSSL 3.6.3 unavailable; no model fallback')
    p=subprocess.run([str(OPENSSL),*args],cwd=ROOT,env={'PATH':'/usr/bin:/bin','LC_ALL':'C','OPENSSL_CONF':'/dev/null'},capture_output=True,text=True,timeout=15)
    return {'argv':['openssl3',*args],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def probe():
    v=command(['version']);help=command(['verify','-help']);xhelp=command(['x509','-help'])
    if v['stdout'].strip()!=VERSION:raise RuntimeError('unsupported OpenSSL version; expected pinned existing 3.6.3')
    for option in ('-verify_hostname','-purpose','-attime','-no-CAfile','-no-CApath','-no-CAstore'):assert option in help['stdout']+help['stderr'],option
    for option in ('-not_before','-not_after'):assert option in xhelp['stdout']+xhelp['stderr'],option
    return {'version':v,'verifyHelp':help,'x509Help':xhelp,'defaultTool':'LibreSSL 3.3.6; verify help lacks -verify_hostname; not used'}

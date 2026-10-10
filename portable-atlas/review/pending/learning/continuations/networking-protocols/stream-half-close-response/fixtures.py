import sys
sys.dont_write_bytecode=True
FIXTURES=[
 dict(id='ping',label='完全PING',wire='000450494e47'),
 dict(id='utf8',label='UTF-8 π / 2bytes',wire='0002cf80'),
 dict(id='maximum',label='本文16bytes',wire='00104142434445464748494a4b4c4d4e4f50'),
 dict(id='header',label='header途中EOF',wire='00'),
 dict(id='body',label='body途中EOF',wire='00045049'),
 dict(id='empty',label='空stream EOF',wire=''),
 dict(id='zero',label='長さ0拒否',wire='0000'),
 dict(id='over',label='長さ17拒否',wire='0011'),
 dict(id='trailing',label='余分bytes拒否',wire='0001505a')]

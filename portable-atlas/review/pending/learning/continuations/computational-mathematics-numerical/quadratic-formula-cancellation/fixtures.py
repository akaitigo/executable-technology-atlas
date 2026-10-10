FIXTURES = [
 dict(id='ordinary',roots=['1','2'],scale='1'),
 dict(id='fnc-separated',roots=['1e-6','1e6'],scale='1'),
 dict(id='severe',roots=['1e-16','1e16'],scale='1'),
 dict(id='scaled-severe',roots=['1e-16','1e16'],scale='1e-12'),
 dict(id='negative',roots=['-1e6','-1e-6'],scale='1'),
 dict(id='mixed',roots=['-2','3'],scale='1'),
 dict(id='zero',roots=['0','2'],scale='1'),
 dict(id='double-zero',roots=['0','0'],scale='1'),
 dict(id='near-double',roots=['1','1.00000001'],scale='1'),
 dict(id='rounded-double',roots=['1','1.0000000000000001'],scale='1'),
]

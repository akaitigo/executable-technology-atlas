from html.parser import HTMLParser
import collections,hashlib,json
NAMES=['api.html','ja.html','guide.html']
class PageParser(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.ids=[];self.links=[];self.stack=[]
    def handle_starttag(self,tag,attrs):
        if tag not in ['html','body','h1','h2','p','a']:raise ValueError('UNSUPPORTED_HTML')
        if len({k for k,v in attrs})!=len(attrs) or any(k not in ['id','href'] for k,v in attrs):raise ValueError('UNSUPPORTED_HTML')
        self.stack.append(tag)
        for k,v in attrs:
            if v is None:raise ValueError('UNSUPPORTED_HTML')
            if k=='id':self.ids.append(v)
            if k=='href':self.links.append(v)
    def handle_endtag(self,tag):
        if not self.stack or self.stack.pop()!=tag:raise ValueError('UNSUPPORTED_HTML')
    def handle_startendtag(self,tag,attrs):raise ValueError('UNSUPPORTED_HTML')
def validate(root,mode):
    reads=[];parsed={}
    base=dict(passed=False,anchors={},links=[],source_revision=None,translation_source_revision=None,target_file=None,fragment=None,anchor_matches=None,translation_fresh=None,reads=reads)
    for name in NAMES:
        data=(root/name).read_bytes();reads.append(dict(path=name,raw=data.decode(),sha256=hashlib.sha256(data).hexdigest()))
    mbytes=(root/'manifest.json').read_bytes();manifest=json.loads(mbytes);reads.append(dict(path='manifest.json',raw=mbytes.decode(),sha256=hashlib.sha256(mbytes).hexdigest()))
    for name,row in zip(NAMES,reads):
        try:
            p=PageParser();p.feed(row['raw']);p.close()
            if p.stack:raise ValueError('UNSUPPORTED_HTML')
        except ValueError as error:return dict(base,status='INPUT_REJECTED',reason=str(error))
        parsed[name]=p
    base.update(anchors={n:p.ids for n,p in parsed.items()},links=parsed['guide.html'].links,source_revision=manifest['source']['revision'],translation_source_revision=manifest['translation']['sourceRevision'])
    if len(base['links'])!=1:return dict(base,status='INPUT_REJECTED',reason='LINK_SUBSET')
    href=base['links'][0];base['translation_fresh']=base['source_revision']==base['translation_source_revision']
    if '://' in href:return dict(base,status='INPUT_REJECTED',reason='EXTERNAL_URL')
    if not href.startswith('api.html#') or href.count('#')!=1:return dict(base,status='INPUT_REJECTED',reason='OUTSIDE_PATH')
    file,fragment=href.split('#');base.update(target_file=file,fragment=fragment,anchor_matches=collections.Counter(parsed[file].ids)[fragment])
    if mode=='file-only':
        failed=base['anchor_matches']!=1 or not base['translation_fresh']
        return dict(base,status='BAD_PASSED' if failed else 'PASSED',passed=(root/file).is_file())
    status='BROKEN_ANCHOR' if not base['anchor_matches'] else 'AMBIGUOUS_ANCHOR' if base['anchor_matches']!=1 else 'STALE_TRANSLATION' if not base['translation_fresh'] else 'PASSED'
    return dict(base,status=status,passed=status=='PASSED')

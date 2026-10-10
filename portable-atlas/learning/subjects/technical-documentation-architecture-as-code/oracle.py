"""独立の固定期待表・locator・hash/文書構造検査。生成器をimportしない。"""
import hashlib,json,re,xml.etree.ElementTree as ET
EXPECTED={
 'baseline':('passed',[],['0\n','0\n','7\n','10\n','10\n','5\n','0\n','0\n']),
 'stale-contract':('rejected',['stale-contract'],[]),
 'regenerated':('passed',[],['0\n','0\n','7\n','10\n','8\n','5\n','0\n','0\n']),
 'stale-code':('rejected',['stale-code'],[]),
 'broken-anchor':('rejected',['broken-local-anchor'],[]),
 'unsupported-function':('rejected',['unsupported function'],[]),
 'wrong-output':('rejected',['snippet-output'],['0\n','0\n','7\n','10\n','10\n','5\n','0\n','0\n']),
 'tampered-svg':('rejected',['artifact-digest:architecture.svg'],[])
}
LOCATORS={
 'examples':'https://docs.python.org/3/library/doctest.html#how-it-works',
 'markdown':'https://spec.commonmark.org/0.31.2/#fenced-code-blocks',
 'svg':'https://www.w3.org/TR/SVG2/struct.html#SVGElement',
 'decisions':'https://adr.github.io/'
}
def sha(data): return hashlib.sha256(data if isinstance(data,bytes) else data.encode('utf-8')).hexdigest()
def verify(row):
    status,failures,outputs=EXPECTED[row['scenario']]; r=row['result']
    assert (r['status'],r['failures'],[x['stdout'] for x in r['snippets']])==(status,failures,outputs)
    for name,raw in row['artifacts'].items(): assert sha(raw)==row['observedArtifactSha256'][name]
    md=row['artifacts']['api.md']
    for label,url in LOCATORS.items(): assert f'[{label}]({url})' in md
    tree=ET.fromstring(row['artifacts']['architecture.svg']); ns={'s':'http://www.w3.org/2000/svg'}
    assert tree.tag=='{http://www.w3.org/2000/svg}svg' and tree.attrib['viewBox']=='0 0 600 200'
    assert len(tree.findall('s:rect',ns))==3 and len(tree.findall('s:path',ns))==2
    if row['scenario']!='tampered-svg': assert [x.text for x in tree.findall('s:text',ns)]==['JSON契約','生成Markdown / SVG','snippet実行']
    if row['scenario']!='broken-anchor':
        assert re.findall(r'<a id="([^"]+)"',md)==['api-clamp','api-add']
        assert re.findall(r'\]\(#([^)]*)\)',md)==['api-clamp','api-add']
    return {'expectedStatus':status,'expectedFailures':failures,'expectedStdout':outputs,'locatorAndArtifactStructure':'passed'}

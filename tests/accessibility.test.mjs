import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';

const root=process.cwd();const page=await readFile(path.join(root,'app/page.tsx'),'utf8');const layout=await readFile(path.join(root,'app/layout.tsx'),'utf8');const css=await readFile(path.join(root,'app/globals.css'),'utf8');
test('日本語文書とskip linkを提供する',()=>{assert.match(layout,/html lang="ja"/);assert.match(page,/className="skip-link"/);assert.match(page,/id="atlas-results"/);});
test('検索結果更新を支援技術へ通知する',()=>{assert.match(page,/role="status" aria-live="polite"/);});
test('Facetをlabelとselectで関連付ける',()=>{assert.match(page,/function Facet/);assert.match(page,/<label className=/);assert.match(page,/<select value=/);});
test('Reduced Motionと可視Focusを提供する',()=>{assert.match(css,/prefers-reduced-motion/);assert.match(css,/:focus-visible/);});

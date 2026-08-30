import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';

const root=process.cwd();const page=await readFile(path.join(root,'app/page.tsx'),'utf8');const layout=await readFile(path.join(root,'app/layout.tsx'),'utf8');const css=await readFile(path.join(root,'app/globals.css'),'utf8');
test('日本語文書とskip linkを提供する',()=>{assert.match(layout,/html lang="ja"/);assert.match(page,/className="skip-link"/);assert.match(page,/id="atlas-results"/);});
test('検索結果更新を支援技術へ通知する',()=>{assert.match(page,/role="status" aria-live="polite"/);});
test('Facetをlabelとselectで関連付ける',()=>{assert.match(page,/function Facet/);assert.match(page,/<label className=/);assert.match(page,/<select value=/);});
test('Reduced Motionと可視Focusを提供する',()=>{assert.match(css,/prefers-reduced-motion/);assert.match(css,/:focus-visible/);});
test('Portal自身のCompletion Certificateへの日本語導線を提供する',()=>{assert.match(page,/href="#portal-certificate"/);assert.match(page,/id="portal-certificate"/);assert.match(page,/Subjectの完成数と、Portal自身の完成を混ぜない/);});
test('Authority Human Reviewはread-only label・status・alert・安全な一次資料Linkを提供する',()=>{assert.match(page,/href="#authority-review"/);assert.match(page,/id="authority-review"/);assert.match(page,/role="status"/);assert.match(page,/role="alert"/);assert.match(page,/target="_blank" rel="noopener noreferrer"/);assert.match(page,/write_decisions=false/);assert.match(page,/機械proposal \/ Human decisionではない/);assert.doesNotMatch(page,/候補を保存/);});
test('Evidence Dependencyをread-onlyかつCore Gate正本で表示する',()=>{assert.match(page,/href="#evidence-dependency"/);assert.match(page,/id="evidence-dependency"/);assert.match(page,/Core正式main \/ CI成功/);assert.match(page,/digest更新だけを「復旧済み」と表示せず/);assert.match(page,/autoPromotion=false/);assert.match(page,/Missing required output/);assert.match(page,/Proof \/ Closure structure drift/);});
test('Definitive v2をbounded履歴から分離し既知Gapを個別表示する',()=>{assert.match(page,/href="#definitive-v2"/);assert.match(page,/id="definitive-v2"/);assert.match(page,/bounded-complete \/ bounded historical/);assert.match(page,/Authority-derived inventory closure/);assert.match(page,/実Runtime Profile/);assert.match(page,/definitive\.gapIds\.map/);assert.match(page,/readOnly=/);assert.match(page,/autoPromotion=/);});

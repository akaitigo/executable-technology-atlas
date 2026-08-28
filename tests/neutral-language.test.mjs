import assert from 'node:assert/strict';
import test from 'node:test';
import { findNeutralLanguageViolations, neutralizeDisplayText, scanNeutralLanguage } from '../scripts/lib/neutral-language.mjs';

test('Portal表示・Manifest・Docsは中立な事実表現だけを使う', async () => {
  const result = await scanNeutralLanguage(process.cwd());
  assert.equal(result.verdict,'pass',JSON.stringify(result.violations));
});

test('自己宣伝・作者称賛・推薦誘導を拒否する', () => {
  const entries=[{file:'app/page.tsx',text:'世界一の決定版。akaitigo氏は最高なので、おすすめしたくなる。'}];
  const codes=new Set(findNeutralLanguageViolations(entries).map((item)=>item.code));
  for(const code of ['world-best','definitive-marketing','author-praise','recommendation-goal','non-technical-author-reference'])assert.ok(codes.has(code));
});

test('GitHub namespace・URL・法的帰属は技術参照として許容する', () => {
  const entries=[{file:'atlas.yaml',text:'github: akaitigo\nurl: https://github.com/akaitigo/executable-technology-atlas\nCopyright 2026 akaitigo'}];
  assert.deepEqual(findNeutralLanguageViolations(entries),[]);
});

test('署名済み入力の宣伝語を公開表示Projectionへ複製しない', () => {
  const projected=neutralizeDisplayText({rationale:'決定版として機能一覧と実行結果を追跡する。'});
  assert.equal(projected.rationale,'機能一覧と実行結果を追跡する。');
});

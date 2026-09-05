import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';

const PROMOTIONAL_PATTERNS = [
  ['world-best', /世界一|世界最高|world(?:'s)? best/i],
  ['definitive-marketing', /決定版|究極版|ultimate (?:guide|platform|solution)/i],
  ['superlative-marketing', /唯一無二|最高峰|業界最高|最強|圧倒的|比類なき|best-in-class/i],
  ['author-praise', /(?:作者|開発者|akaitigo(?:氏|さん|様)).{0,30}(?:称賛|天才|最高|卓越|素晴らし)/i],
  ['recommendation-goal', /勧めたくなる|薦めたくなる|おすすめしたくなる|推奨したくなる/i],
];

export function neutralizeDisplayText(value) {
  if (typeof value === 'string') return value.includes('決定版') ? value.replaceAll('決定版として', '').replaceAll('決定版の参照経路', '検証可能な参照経路').replaceAll('決定版', '検証可能な参照情報').replace(/\s{2,}/g, ' ').trim() : value;
  if (Array.isArray(value)) return value.map(neutralizeDisplayText);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key,item]) => [key,neutralizeDisplayText(item)]));
  return value;
}

export function findNeutralLanguageViolations(entries) {
  const violations = [];
  for (const { file, text } of entries) for (const [offset,line] of text.split('\n').entries()) {
    for (const [code,pattern] of PROMOTIONAL_PATTERNS) if (pattern.test(line)) violations.push({ code, file, line:offset+1, text:line.trim().slice(0,240) });
    if (/akaitigo/i.test(line)) {
      const technical = line
        .replace(/https:\/\/github\.com\/akaitigo[^\s)"']*/gi, '')
        .replace(/github\.com\/akaitigo[^\s)"']*/gi, '')
        .replace(/\b(?:github|owner):\s*akaitigo\b/gi, '')
        .replace(/"(?:github|owner)"\s*:\s*"akaitigo"/gi, '')
        .replace(/Copyright\s+\d{4}\s+akaitigo/gi, '');
      if (/akaitigo/i.test(technical)) violations.push({ code:'non-technical-author-reference', file, line:offset+1, text:line.trim().slice(0,240) });
    }
  }
  return violations;
}

async function markdownFiles(directory) {
  const result = [];
  for (const entry of await readdir(directory,{withFileTypes:true})) {
    const absolute = path.join(directory,entry.name);
    if (entry.isDirectory()) result.push(...await markdownFiles(absolute));
    else if (/\.(md|json|ya?ml|tsx)$/.test(entry.name)) result.push(absolute);
  }
  return result;
}

export async function scanNeutralLanguage(root = process.cwd()) {
  const explicit = ['README.md','NOTICE','atlas.yaml','mastery.yaml','coverage.yaml','skill.package.yaml','sources.lock.yaml','provenance.yaml','release/manifest.json','evidence/completion-certificate.json','third_party/manifest.yaml','app/page.tsx','app/layout.tsx'];
  const discovered = [
    ...await markdownFiles(path.join(root,'docs')),
    ...await markdownFiles(path.join(root,'claims')),
    ...await markdownFiles(path.join(root,'.agents/skills/technology-atlas-router')),
    ...await markdownFiles(path.join(root,'public/data/releases')),
  ];
  const files = [...new Set([...explicit.map((file)=>path.join(root,file)),...discovered])].sort();
  const entries = await Promise.all(files.map(async (absolute) => ({ file:path.relative(root,absolute), text:await readFile(absolute,'utf8') })));
  const violations = findNeutralLanguageViolations(entries);
  return { verdict:violations.length?'fail':'pass', filesScanned:entries.length, violations };
}

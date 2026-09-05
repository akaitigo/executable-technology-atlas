import { spawnSync } from 'node:child_process';
import path from 'node:path';

export const FIXED_CORE_CHECKOUT_PATH='/private/tmp/reference-atlas-core-072-git';

function probeGitHead(candidate){
  const result=spawnSync('git',['rev-parse','HEAD'],{cwd:candidate,encoding:'utf8'});
  return{status:result.status??1,commit:result.stdout?.trim()??'',stderr:result.stderr?.trim()??''};
}

export function buildCoreCheckoutCandidates(root,{env=process.env}={}){
  const candidates=[];
  if(env.ATLAS_CORE_DIR)candidates.push({path:path.resolve(env.ATLAS_CORE_DIR),source:'env',strict:true});
  candidates.push({path:FIXED_CORE_CHECKOUT_PATH,source:'fixed-tmp',strict:false});
  candidates.push({path:path.resolve(root,'..','reference-atlas-core'),source:'adjacent',strict:false});
  const seen=new Set();
  return candidates.filter((item)=>{if(seen.has(item.path))return false;seen.add(item.path);return true;});
}

export function resolveCoreCheckout(root,expectedCommit,{env=process.env,probe=probeGitHead}={}){
  const candidates=buildCoreCheckoutCandidates(root,{env});
  const errors=[];
  for(const candidate of candidates){
    const observed=probe(candidate.path);
    if(observed.status===0&&observed.commit===expectedCommit)return{coreDir:candidate.path,source:candidate.source,expectedCommit};
    errors.push(`${candidate.source}:${candidate.path}:${observed.commit||observed.stderr||`status=${observed.status}`}`);
    if(candidate.strict)throw new Error(`ATLAS_CORE_DIR does not match required commit ${expectedCommit}: ${errors.at(-1)}`);
  }
  throw new Error(`Core checkoutが正式main固定commitではありません: ${errors.join(' | ')}`);
}

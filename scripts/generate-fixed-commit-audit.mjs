#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fixtureKeyPair, sha256, signDigest } from './lib/crypto.mjs';

const root=process.cwd();
const coreCommit='072d7ca77981f51754e824d70c6d4ecd55ea67e5';
const gate=(command,result,summary,diagnostics=[])=>({command,result,summary,diagnostics});
const observations=[
  {
    subjectId:'argocd',atlasId:'argocd-reference-atlas',repository:'argocd-reference-atlas',commit:'37db7c88c0f365c730d95472ce74a40fedebced9',environment:'ARG0CD_ATLAS_REPOSITORY',
    paths:['atlas.yaml','definitive.yaml','evidence/dependency-graph.json','authority/extraction.snapshot.json','authority/body-inventory.snapshot.json','authority/review-queue.snapshot.json','evidence/scenarios/index.json'],
    manifest:{status:'incomplete',completionClass:'incomplete',targets:30,openRequired:22,claims:22,evidence:24},
    core:{
      audit:gate('atlas audit .','pass',{completionClass:'incomplete',targets:30,claims:22,evidence:24,openRequired:22}),
      evidenceDependency:gate('atlas audit . --gate evidence-dependency','pass',{inputs:15,changedInputs:0,outputs:1060,affectedOutputs:0,runs:30}),
      authorityExtraction:gate('atlas audit . --gate authority-extraction','pass',{status:'incomplete-human-review-required',candidateEdges:76,classifiedEdges:76,humanReviewed:0,coreV2Eligible:0}),
      authorityBody:gate('atlas audit . --gate authority-body','pass',{status:'incomplete-human-review-required',candidateAnchors:63889,classified:0,unclassified:63889,humanReviewed:0,coreV2Eligible:0}),
      authorityReview:gate('atlas audit . --gate authority-review','pass',{status:'incomplete-human-review-required',queued:63889,pendingHuman:63889,humanReviewed:0,decisions:0}),
      definitive:gate('atlas audit . --gate definitive','fail',{completionClass:'not-definitive'},['depth.parity.yamlが固定commitに存在しません'])
    },
    gaps:[
      {id:'fixed-release-manifest-missing',status:'open',detail:'署名済み固定Release Manifestがありません。',count:1},
      {id:'public-trust-key-missing',status:'open',detail:'公開Release Trust Keyがありません。',count:1},
      {id:'definitive-certificate-missing',status:'open',detail:'Core v2 Definitive Certificateがありません。',count:1},
      {id:'depth-parity-missing',status:'open',detail:'Definitive Gate必須のdepth.parity.yamlがありません。',count:1},
      {id:'authority-human-review-open',status:'open',detail:'Authority anchorがhuman review未完了です。',count:63889},
      {id:'open-required-targets',status:'open',detail:'必須TargetがClosureしていません。',count:22},
      {id:'scenario-proof-schema-drift',status:'open',detail:'Scenario Proof Indexが固定Core Schemaと一致しません。',count:1}
    ]
  },
  {
    subjectId:'postgresql',atlasId:'postgresql-reference-atlas',repository:'postgresql-reference-atlas',commit:'94353f5145a419e585fd73ec7dd496dc79f3f0e9',environment:'POSTGRESQL_ATLAS_REPOSITORY',
    paths:['atlas.yaml','definitive.yaml','depth.parity.yaml','evidence/dependency-graph.json','authority/extraction.snapshot.json','authority/body-inventory.snapshot.json','authority/review-queue.snapshot.json','evidence/scenarios/index.json','evidence/scenarios/closure-plan.json'],
    manifest:{status:'incomplete',completionClass:'incomplete',targets:56,openRequired:27,claims:30,evidence:31},
    core:{
      audit:gate('atlas audit .','pass',{completionClass:'incomplete',targets:56,claims:30,evidence:31,openRequired:27}),
      evidenceDependency:gate('atlas audit . --gate evidence-dependency','pass',{inputs:11,changedInputs:4,outputs:435,affectedOutputs:435,runs:1}),
      authorityExtraction:gate('atlas audit . --gate authority-extraction','pass',{status:'incomplete-human-review-required',locked:10,matched:0,failed:10,candidateEdges:10,classifiedEdges:10,unclassifiedEdges:0,deferredLocators:10,humanReviewed:0,coreV2Eligible:0}),
      authorityBody:gate('atlas audit . --gate authority-body','pass',{status:'incomplete-human-review-required',sources:10,documents:398,matched:390,failed:8,candidateAnchors:5512,classified:0,unclassified:5512,humanReviewed:0,coreV2Eligible:0}),
      authorityReview:gate('atlas audit . --gate authority-review','pass',{status:'incomplete-human-review-required',queued:5512,pendingHuman:5512,humanReviewed:0,unavailableHolds:8,decisions:0}),
      definitive:gate('atlas audit . --gate definitive','fail',{completionClass:'not-definitive'},['required Target query.sql-commandsはpartialです'])
    },
    gaps:[
      {id:'fixed-release-manifest-missing',status:'open',detail:'署名済み固定Release Manifestがありません。',count:1},
      {id:'public-trust-key-missing',status:'open',detail:'公開Release Trust Keyがありません。',count:1},
      {id:'definitive-certificate-missing',status:'open',detail:'Core v2 Definitive Certificateがありません。',count:1},
      {id:'open-required-targets',status:'open',detail:'必須TargetがClosureしていません。',count:27},
      {id:'authority-locator-extraction-failed',status:'open',detail:'Authority locator extractionが失敗またはdeferです。',count:10},
      {id:'authority-body-unclassified',status:'open',detail:'Authority body anchorが未分類です。',count:5512},
      {id:'authority-human-review-open',status:'open',detail:'Authority anchorがhuman review未完了です。',count:5512},
      {id:'authority-unavailable-holds',status:'open',detail:'一次資料がunavailable holdです。',count:8},
      {id:'scenario-runtime-gaps',status:'open',detail:'Scenario runtime closure gapが残っています。',count:278}
    ]
  }
];

const {privateKey,publicKeyPem}=fixtureKeyPair();
const keyId=`fixture-ed25519-${sha256(publicKeyPem).slice(7,23)}`;
for(const observation of observations){
  const sourceRoot=path.resolve(process.env[observation.environment]??path.join(root,'..',observation.repository));
  const tree=execFileSync('git',['rev-parse',`${observation.commit}^{tree}`],{cwd:sourceRoot,encoding:'utf8'}).trim();
  const artifactDigests=observation.paths.map((relative)=>({path:relative,digest:sha256(execFileSync('git',['show',`${observation.commit}:${relative}`],{cwd:sourceRoot}))}));
  const payload={subjectId:observation.subjectId,atlasId:observation.atlasId,repository:observation.repository,sourceCommit:observation.commit,sourceTree:tree,sourceMode:'fixed-clean-commit',releaseBoundary:{status:'unpublished-fixed-commit',tag:null,signedManifest:false,publicTrustKey:false,definitiveCertificate:false},manifest:observation.manifest,core:{commit:coreCommit,...observation.core},artifactDigests,gaps:observation.gaps,readOnly:true,autoPromotion:false};
  const digest=sha256(payload);
  const envelope={schemaVersion:1,kind:'portal-fixed-commit-audit',attestation:{digest,observedAt:'2026-08-31T00:00:00Z'},signature:{algorithm:'Ed25519',keyId,value:signDigest(digest,privateKey),identity:'portal-fixture-observation-only'},payload};
  const output=path.join(root,`fixtures/fixed-commit-audits/${observation.subjectId}@${observation.commit}.json`);
  await mkdir(path.dirname(output),{recursive:true});
  await writeFile(output,`${JSON.stringify(envelope,null,2)}\n`);
  console.log(`Fixed commit audit生成済み: ${observation.subjectId}@${observation.commit} ${digest}`);
}

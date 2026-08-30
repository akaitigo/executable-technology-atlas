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
  },
  {
    subjectId:'flutter',atlasId:'flutter-reference-atlas',repository:'flutter-reference-atlas',commit:'45980f048800d267155e0ec895c0b2174e3e31f6',environment:'FLUTTER_ATLAS_REPOSITORY',
    paths:['atlas.yaml','coverage.yaml','mastery.yaml','evidence/dependency-graph.json','authority/extraction.snapshot.json','authority/body-inventory.snapshot.json','authority/review-queue.snapshot.json','evidence/scenarios/index.json','evidence/scenarios/closure-plan.json'],
    manifest:{status:'incomplete',completionClass:'incomplete',targets:27,openRequired:2,claims:29,evidence:8},
    core:{
      audit:gate('atlas audit .','pass',{completionClass:'incomplete',targets:27,claims:29,evidence:8,openRequired:2}),
      evidenceDependency:gate('atlas audit . --gate evidence-dependency','fail',{inputs:19,outputs:742,runs:14,missingRequiredOutputs:1},['required output evidence/scenarios/surfaces/build/android/boundary.proof.jsonが固定commitに存在しません']),
      authorityExtraction:gate('atlas audit . --gate authority-extraction','fail',{status:'schema-drift',locked:12,deferredLocators:107,humanReviewed:0,coreV2Eligible:0},['authority-extraction.snapshot.jsonが固定Core v2 Schemaと一致しません']),
      authorityBody:gate('atlas audit . --gate authority-body','fail',{status:'schema-drift',candidateAnchors:74,classified:0,unclassified:74,humanReviewed:0,coreV2Eligible:0},['authority/body-inventory.snapshot.jsonが固定Core v2 Schemaと一致しません']),
      authorityReview:gate('atlas audit . --gate authority-review','fail',{status:'schema-drift',queued:74,pendingHuman:74,humanReviewed:0,unavailableHolds:3,decisions:0},['Authority body schema driftのためreview gateを通過しません']),
      definitive:gate('atlas audit . --gate definitive','fail',{completionClass:'not-definitive',missingContractArtifacts:3},['definitive.yaml、depth.parity.yaml、verification.matrix.yamlが固定commitに存在しません']),
      scenarioTrace:gate('atlas audit . --gate scenario-trace','fail',{status:'schema-drift',rows:540,runtimeRows:9,gaps:531},['evidence/scenarios/index.jsonが固定Core v2 Scenario Proof Schemaと一致しません']),
      nonRegression:gate('atlas audit . --gate non-regression','fail',{missingContractArtifacts:1},['non-regression.yamlが固定commitに存在しません']),
      evidenceDurability:gate('atlas audit . --gate evidence-durability','fail',{missingRequiredOutputs:1},['artifacts/pattern-scenarios/results.jsonが固定commitに存在しません'])
    },
    gaps:[
      {id:'fixed-release-manifest-missing',status:'open',detail:'署名済み固定Release Manifestがありません。',count:1},
      {id:'public-trust-key-missing',status:'open',detail:'公開Release Trust Keyがありません。',count:1},
      {id:'definitive-certificate-missing',status:'open',detail:'Core v2 Definitive Certificateがありません。',count:1},
      {id:'open-required-targets',status:'open',detail:'必須TargetがClosureしていません。',count:2},
      {id:'evidence-dependency-required-output-missing',status:'open',detail:'Evidence Dependency Graphの必須outputが固定commitにありません。',count:1},
      {id:'authority-extraction-schema-drift',status:'open',detail:'Authority extraction snapshotが固定Core v2 Schemaと一致しません。',count:1},
      {id:'authority-locator-evaluation-deferred',status:'open',detail:'Authority locator評価がdeferされています。',count:107},
      {id:'authority-body-schema-drift',status:'open',detail:'Authority body inventoryが固定Core v2 Schemaと一致しません。',count:1},
      {id:'authority-body-unclassified',status:'open',detail:'Authority body anchorが未分類です。',count:74},
      {id:'authority-human-review-open',status:'open',detail:'Authority anchorがhuman review未完了です。',count:74},
      {id:'authority-stale-holds',status:'open',detail:'Authority一次資料がstale holdです。',count:3},
      {id:'definitive-contract-artifacts-missing',status:'open',detail:'Definitive、Depth parity、Verification matrixがありません。',count:3},
      {id:'scenario-proof-schema-drift',status:'open',detail:'Scenario Proof Indexが固定Core v2 Schemaと一致しません。',count:1},
      {id:'scenario-runtime-gaps',status:'open',detail:'Scenario runtime closure gapが残っています。',count:531},
      {id:'non-regression-contract-missing',status:'open',detail:'Non-regression契約が固定commitにありません。',count:1},
      {id:'evidence-durability-output-missing',status:'open',detail:'Evidence durabilityの必須outputが固定commitにありません。',count:1}
    ]
  },
  {
    subjectId:'rabbitmq',atlasId:'rabbitmq-reference-atlas',repository:'rabbitmq-reference-atlas',commit:'a500e567648cb076a1498a2ddc7b9f5393ce3c2f',environment:'RABBITMQ_ATLAS_REPOSITORY',
    paths:['atlas.yaml','definitive.yaml','evidence/completion-certificate.json','evidence/dependency-graph.json','authority/extraction.snapshot.json','authority/body-inventory.snapshot.json','authority/review-queue.snapshot.json','evidence/scenarios/index.json','evidence/scenarios/closure-plan.json'],
    manifest:{status:'incomplete',completionClass:'incomplete',targets:238,openRequired:203,claims:206,evidence:33},
    core:{
      audit:gate('atlas audit .','pass',{completionClass:'incomplete',targets:238,claims:206,evidence:33,openRequired:203}),
      evidenceDependency:gate('atlas audit . --gate evidence-dependency','pass',{inputs:14,changedInputs:2,outputs:2397,affectedOutputs:2363,runs:63}),
      authorityExtraction:gate('atlas audit . --gate authority-extraction','fail',{status:'schema-drift',locked:50,matched:48,failed:0,staleSources:2,candidateEdges:206,classifiedEdges:206,unclassifiedEdges:0,deferredLocators:0,humanReviewed:0,coreV2Eligible:0},['authority/extraction.snapshot.jsonが固定Core v2 Schemaと一致しません']),
      authorityBody:gate('atlas audit . --gate authority-body','fail',{status:'schema-drift',sources:50,documents:50,matched:48,staleDocuments:2,candidateAnchors:1579,classified:0,unclassified:1579,humanReviewed:0,coreV2Eligible:0},['authority/body-inventory.snapshot.jsonが固定Core v2 Schemaと一致しません']),
      authorityReview:gate('atlas audit . --gate authority-review','fail',{status:'schema-drift',queued:1579,pendingHuman:1579,humanReviewed:0,unavailableHolds:2,decisions:0},['Authority body schema driftのためreview gateを通過しません']),
      definitive:gate('atlas audit . --gate definitive','fail',{completionClass:'not-definitive',declaredCompletionClass:'subject-definitive',missingContractArtifacts:2},['自己宣言のsubject-definitiveはCore Gate結果ではありません','verification.matrix.yamlとdepth.parity.yamlが固定commitに存在しません']),
      scenarioTrace:gate('atlas audit . --gate scenario-trace','fail',{status:'schema-drift',rows:2060,runtimeRows:26,gaps:925},['evidence/scenarios/index.jsonが固定Core v2 Scenario Proof Schemaと一致しません']),
      nonRegression:gate('atlas audit . --gate non-regression','fail',{missingContractArtifacts:1},['non-regression.yamlが固定commitに存在しません']),
      evidenceDurability:gate('atlas audit . --gate evidence-durability','fail',{missingRequiredOutputs:1},['artifacts/pattern-scenarios/results.jsonが固定commitに存在しません'])
    },
    gaps:[
      {id:'fixed-release-manifest-missing',status:'open',detail:'署名済み固定Release Manifestがありません。',count:1},
      {id:'public-trust-key-missing',status:'open',detail:'公開Release Trust Keyがありません。',count:1},
      {id:'definitive-certificate-missing',status:'open',detail:'Core v2 Definitive Certificateがありません。',count:1},
      {id:'open-required-targets',status:'open',detail:'必須TargetがClosureしていません。',count:203},
      {id:'historical-certificate-schema-drift',status:'open',detail:'既存Completion Certificateは固定Core v2 Schemaに適合せず署名もありません。',count:1},
      {id:'authority-extraction-schema-drift',status:'open',detail:'Authority extraction snapshotが固定Core v2 Schemaと一致しません。',count:1},
      {id:'authority-source-stale',status:'open',detail:'Authority一次資料の固定digestと取得digestが一致しません。',count:2},
      {id:'authority-body-schema-drift',status:'open',detail:'Authority body inventoryが固定Core v2 Schemaと一致しません。',count:1},
      {id:'authority-body-unclassified',status:'open',detail:'Authority body anchorが未分類です。',count:1579},
      {id:'authority-human-review-open',status:'open',detail:'Authority anchorがhuman review未完了です。',count:1579},
      {id:'authority-stale-holds',status:'open',detail:'Authority一次資料がstale holdです。',count:2},
      {id:'definitive-self-declaration-rejected',status:'open',detail:'definitive.yamlのsubject-definitive自己宣言はCore Gate失敗のため完成扱いできません。',count:1},
      {id:'definitive-contract-artifacts-missing',status:'open',detail:'Verification matrixとDepth parityが固定commitにありません。',count:2},
      {id:'scenario-proof-schema-drift',status:'open',detail:'Scenario Proof Indexが固定Core v2 Schemaと一致しません。',count:1},
      {id:'scenario-runtime-gaps',status:'open',detail:'Scenario runtime closure gapが残っています。',count:925},
      {id:'non-regression-contract-missing',status:'open',detail:'Non-regression契約が固定commitにありません。',count:1},
      {id:'evidence-durability-output-missing',status:'open',detail:'Evidence durabilityの必須outputが固定commitにありません。',count:1}
    ]
  },
  {
    subjectId:'kotlin',atlasId:'kotlin-reference-atlas',repository:'kotlin-reference-atlas',commit:'39da6284576c5bafae4921ba7578090ca5603318',environment:'KOTLIN_ATLAS_REPOSITORY',
    paths:['atlas.yaml','definitive.yaml','depth.parity.yaml','verification.matrix.yaml','non-regression.yaml','migrations/definitive-v2.yaml','evidence/dependency-graph.json','authority/extraction.snapshot.json','authority/body-inventory.snapshot.json','authority/review-queue.snapshot.json','evidence/scenarios/index.json','evidence/scenarios/closure-plan.json','artifacts/pattern-scenarios/results.json'],
    manifest:{status:'incomplete',completionClass:'incomplete',targets:33,openRequired:3,claims:31,evidence:32},
    core:{
      audit:gate('atlas audit .','pass',{completionClass:'incomplete',targets:33,claims:31,evidence:32,openRequired:3}),
      evidenceDependency:gate('atlas audit . --gate evidence-dependency','pass',{inputs:4,changedInputs:4,outputs:777,affectedOutputs:777,runs:1}),
      authorityExtraction:gate('atlas audit . --gate authority-extraction','pass',{status:'incomplete-source-state',locked:18,matched:0,failed:18,staleSources:0,candidateEdges:18,classifiedEdges:0,unclassifiedEdges:18,deferredLocators:18,humanReviewed:0,coreV2Eligible:0},['18 Sourceのlocator評価がdeferされ、Core v2 eligible surfaceは0です']),
      authorityBody:gate('atlas audit . --gate authority-body','pass',{status:'incomplete-human-review-required',sources:18,documents:16,matched:16,staleDocuments:0,candidateAnchors:146402,classified:0,unclassified:146402,humanReviewed:0,coreV2Eligible:0},['146402 anchorが未分類でhuman review未完了です']),
      authorityReview:gate('atlas audit . --gate authority-review','pass',{status:'incomplete-human-review-required',queued:146402,pendingHuman:146402,humanReviewed:0,unavailableHolds:0,decisions:0},['0 decisionは進捗またはDepth達成として扱えません']),
      definitive:gate('atlas audit . --gate definitive','fail',{completionClass:'not-definitive',declaredCompletionClass:'subject-definitive',openRequired:3},['required Target authority.locator-extractionはpartialです']),
      scenarioTrace:gate('atlas audit . --gate scenario-trace','pass',{status:'incomplete-runtime-proof-required',rows:690,runtimeRows:0,gaps:690},['Gate契約は有効ですが、全690 rowがPattern-specific runtime gapです']),
      nonRegression:gate('atlas audit . --gate non-regression','pass',{baselineItems:220,currentItems:2868,replacements:5}),
      evidenceDurability:gate('atlas audit . --gate evidence-durability','fail',{status:'failed',total:0,passed:0,failed:0},['failed runを成功Evidence directoryへ公開できません'])
    },
    gaps:[
      {id:'fixed-release-manifest-missing',status:'open',detail:'署名済み固定Release Manifestがありません。',count:1},
      {id:'public-trust-key-missing',status:'open',detail:'公開Release Trust Keyがありません。',count:1},
      {id:'definitive-certificate-missing',status:'open',detail:'Core v2 Definitive Certificateがありません。',count:1},
      {id:'open-required-targets',status:'open',detail:'必須TargetがClosureしていません。',count:3},
      {id:'authority-locator-extraction-failed',status:'open',detail:'Authority locator extractionが失敗またはdeferです。',count:18},
      {id:'authority-reference-edges-unclassified',status:'open',detail:'Authority reference edgeが未分類です。',count:18},
      {id:'authority-body-unclassified',status:'open',detail:'Authority body anchorが未分類です。',count:146402},
      {id:'authority-human-review-open',status:'open',detail:'Authority anchorがhuman review未完了です。',count:146402},
      {id:'depth-parity-incomplete',status:'open',detail:'Depth parityはincompleteでrowがありません。',count:1},
      {id:'definitive-self-declaration-rejected',status:'open',detail:'definitive.yamlのsubject-definitive自己宣言はCore Gate失敗のため完成扱いできません。',count:1},
      {id:'definitive-required-target-partial',status:'open',detail:'Definitive Gate必須Target authority.locator-extractionがpartialです。',count:1},
      {id:'scenario-runtime-gaps',status:'open',detail:'Pattern-specific Scenario runtime proofがありません。',count:690},
      {id:'evidence-durability-failed',status:'open',detail:'Evidence durability artifactはstatus=failedで実行結果が0件です。',count:1}
    ]
  }
];

const {privateKey,publicKeyPem}=fixtureKeyPair();
const keyId=`fixture-ed25519-${sha256(publicKeyPem).slice(7,23)}`;
for(const observation of observations){
  const sourceRoot=path.resolve(process.env[observation.environment]??path.join(root,'..',observation.repository));
  const tree=execFileSync('git',['rev-parse',`${observation.commit}^{tree}`],{cwd:sourceRoot,encoding:'utf8'}).trim();
  const artifactDigests=observation.paths.map((relative)=>({path:relative,digest:sha256(execFileSync('git',['show',`${observation.commit}:${relative}`],{cwd:sourceRoot,maxBuffer:16*1024*1024}))}));
  const payload={subjectId:observation.subjectId,atlasId:observation.atlasId,repository:observation.repository,sourceCommit:observation.commit,sourceTree:tree,sourceMode:'fixed-clean-commit',releaseBoundary:{status:'unpublished-fixed-commit',tag:null,signedManifest:false,publicTrustKey:false,definitiveCertificate:false},manifest:observation.manifest,core:{commit:coreCommit,...observation.core},artifactDigests,gaps:observation.gaps,readOnly:true,autoPromotion:false};
  const digest=sha256(payload);
  const envelope={schemaVersion:1,kind:'portal-fixed-commit-audit',attestation:{digest,observedAt:'2026-08-31T00:00:00Z'},signature:{algorithm:'Ed25519',keyId,value:signDigest(digest,privateKey),identity:'portal-fixture-observation-only'},payload};
  const output=path.join(root,`fixtures/fixed-commit-audits/${observation.subjectId}@${observation.commit}.json`);
  await mkdir(path.dirname(output),{recursive:true});
  await writeFile(output,`${JSON.stringify(envelope,null,2)}\n`);
  console.log(`Fixed commit audit生成済み: ${observation.subjectId}@${observation.commit} ${digest}`);
}

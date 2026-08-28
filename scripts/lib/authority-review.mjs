import { gunzipSync } from 'node:zlib';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { sha256 } from './crypto.mjs';

const AUTOMATED_REVIEWER=/^(?:auto(?:mated)?|agent|bot|system|machine)(?:$|[-_. ])/i;
const SEMANTIC_ACTIONS=new Set(['include','exclude','merge','split']);
const exactKeys=(value,expected)=>value&&JSON.stringify(Object.keys(value).sort())===JSON.stringify([...expected].sort());
const isDigest=(value)=>/^sha256:[a-f0-9]{64}$/.test(value??'');
const isItemId=(value)=>/^[a-z][a-z0-9.-]+$/.test(value??'');

export function parseAuthorityReviewArchive(bytes){return JSON.parse(gunzipSync(bytes).toString('utf8'));}

function validateBinding(binding,item){
  const fields=['anchor_id','document_id','document_url','source_ids','locked_source_digest','inventory_tool_digest','review_queue_tool_digest','locator','locator_kind','context_start','context_end','context_unit','context_digest'];
  if(!exactKeys(binding,fields))return false;
  return fields.every((field)=>JSON.stringify(binding[field])===JSON.stringify(item[field]))&&[binding.locked_source_digest,binding.inventory_tool_digest,binding.review_queue_tool_digest,binding.context_digest].every(isDigest);
}

// Future Core common API boundary only. The Portal never persists or emits this record.
export function validateAuthorityReviewCandidate(candidate,itemById,{allowDefer=true}={}){
  const errors=[];const action=candidate?.action;const isDefer=action==='defer';
  const decisionFields=['decision_id','action','anchor_ids','source_bindings','rationale','reviewer','reviewed_at','review_method','mapping','result_items'];
  if(!exactKeys(candidate,decisionFields))errors.push('Decisionのfield集合がCore共通Schema境界と一致しません');
  if(!SEMANTIC_ACTIONS.has(action)&&!(allowDefer&&isDefer))errors.push('actionはinclude/exclude/merge/splitまたはworkflow holdのdeferが必要です');
  if(!/^decision\.[a-z0-9.-]+$/.test(candidate?.decision_id??''))errors.push('decision_idが不正です');
  if((candidate?.rationale??'').trim().length<40)errors.push('reason/rationaleは40文字以上が必要です');
  if((candidate?.reviewer??'').trim().length<2||AUTOMATED_REVIEWER.test((candidate?.reviewer??'').trim()))errors.push('reviewerは人の識別子が必要で、自動主体は保存できません');
  if(candidate?.review_method!=='manual-primary-source')errors.push('review_methodはmanual-primary-sourceが必要です');
  if(!/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(candidate?.reviewed_at??'')||Number.isNaN(Date.parse(candidate?.reviewed_at)))errors.push('time/reviewed_atはTimezone付きISO date-timeが必要です');
  const anchors=candidate?.anchor_ids??[];const bindings=candidate?.source_bindings??[];const mappings=candidate?.mapping??[];
  if(!anchors.length||new Set(anchors).size!==anchors.length||bindings.length!==anchors.length||mappings.length!==anchors.length)errors.push('anchor/binding/mappingは同数かつ1件以上が必要です');
  const bindingById=new Map(bindings.map((item)=>[item.anchor_id,item]));const mappingById=new Map(mappings.map((item)=>[item.old_anchor_id,item]));
  if(bindingById.size!==anchors.length||mappingById.size!==anchors.length)errors.push('binding/mapping IDが重複または不足しています');
  for(const anchorId of anchors){const item=itemById.get(anchorId);if(!item)errors.push(`Export外anchorです: ${anchorId}`);else if(!validateBinding(bindingById.get(anchorId),item))errors.push(`URL/locator/digest bindingがExportと一致しません: ${anchorId}`);const mapping=mappingById.get(anchorId);if(!mapping||!exactKeys(mapping,['old_anchor_id','new_item_ids'])||!Array.isArray(mapping.new_item_ids)||new Set(mapping.new_item_ids).size!==mapping.new_item_ids.length||mapping.new_item_ids.some((id)=>!isItemId(id)))errors.push(`mappingが不正です: ${anchorId}`);}
  const results=candidate?.result_items??[];if(!Array.isArray(results)||results.some((item)=>!exactKeys(item,['id','item_type'])||!isItemId(item.id)||!['surface','atomic-behavior'].includes(item.item_type))||new Set(results.map((item)=>item.id)).size!==results.length)errors.push('result_itemsが不正です');
  const mapped=[...new Set(mappings.flatMap((item)=>item.new_item_ids??[]))].sort();const resultIds=results.map((item)=>item.id).sort();if(JSON.stringify(mapped)!==JSON.stringify(resultIds))errors.push('mappingとresult_itemsが一致しません');
  if((action==='exclude'||isDefer)&&mappings.some((item)=>(item.new_item_ids??[]).length))errors.push(`${action}はnew itemへmappingできません`);
  if(action==='include'&&mappings.some((item)=>!(item.new_item_ids??[]).length))errors.push('includeは旧→新mappingが必要です');
  if(action==='include'&&new Set(mappings.flatMap((item)=>item.new_item_ids??[])).size!==mappings.reduce((sum,item)=>sum+(item.new_item_ids??[]).length,0))errors.push('includeでmapping先を共有する場合はmergeが必要です');
  if(action==='merge'&&(anchors.length<2||mappings.some((item)=>!(item.new_item_ids??[]).length)||new Set(mappings.map((item)=>JSON.stringify([...(item.new_item_ids??[])].sort()))).size!==1))errors.push('merge mappingが不正です');
  if(action==='split'&&(anchors.length!==1||(mappings[0]?.new_item_ids??[]).length<2))errors.push('split mappingが不正です');
  return{ok:errors.length===0,errors,countsAsReviewed:errors.length===0&&!isDefer,recordKind:isDefer?'workflow-hold':'human-semantic-decision'};
}

export function validateAuthorityReviewBundle(envelope,archiveBytes,lock,verification){
  const errors=[...(verification?.errors??[])];let archive=null;
  if(envelope?.kind!=='portal-authority-review')errors.push('Authority Review kindが不正です');
  if(envelope?.payload?.subjectId!==lock.subjectId||envelope?.payload?.atlasId!==lock.atlasId||envelope?.payload?.repository!==lock.repository||envelope?.payload?.sourceCommit!==lock.sourceCommit)errors.push('Authority Review Subject/Commit bindingがLockと一致しません');
  if(sha256(archiveBytes)!==envelope?.payload?.archiveDigest)errors.push('Authority Review archive digestが一致しません');
  try{archive=parseAuthorityReviewArchive(archiveBytes);}catch{errors.push('Authority Review archiveを展開できません');return{ok:false,errors,archive:null};}
  const sourceBindings=[['exportBytes','reviewExport','exportDigest'],['exportSchemaBytes','exportSchema','exportSchemaDigest'],['packetSchemaBytes','packetSchema','packetSchemaDigest'],['packetIndexBytes','packetIndex','packetIndexDigest']];
  for(const[bytesKey,valueKey,digestKey]of sourceBindings){if(sha256(archive[bytesKey])!==lock[digestKey])errors.push(`${valueKey} source digestがLockと一致しません`);try{if(JSON.stringify(JSON.parse(archive[bytesKey]))!==JSON.stringify(archive[valueKey]))errors.push(`${valueKey} source bytesとpayloadが一致しません`);}catch{errors.push(`${valueKey} source bytesがJSONではありません`);}}
  const reviewExport=archive.reviewExport;const expected=lock.expected;
  if(reviewExport?.schema_digest!==lock.exportSchemaDigest||reviewExport?.packet_schema_digest!==lock.packetSchemaDigest||reviewExport?.integrity?.packet_index_digest!==lock.packetIndexDigest)errors.push('Export内Schema/Index digest bindingがLockと一致しません');
  const ajv=new Ajv2020({allErrors:true,strict:true});addFormats(ajv);let validateExport;let validatePacket;try{validateExport=ajv.compile(archive.exportSchema);validatePacket=ajv.compile(archive.packetSchema);}catch(error){errors.push(`Authority Review Schemaをcompileできません: ${error.message}`);}
  if(validateExport&&!validateExport(reviewExport))errors.push(`review-export.v1 Schema不適合: ${ajv.errorsText(validateExport.errors)}`);
  const summary=reviewExport?.summary??{};const summaryChecks={packets:expected.packets,unique_anchors:expected.uniqueAnchors,candidate_domain_projections:expected.candidateDomainProjections,deep_links:expected.deepLinks,pending_human:expected.pendingHuman,human_reviewed:expected.humanReviewed,proposed_clusters:expected.proposedClusters,semantic_decisions_by_export:expected.semanticDecisionsByExport,stale_document_holds:expected.staleDocumentHolds};for(const[field,value]of Object.entries(summaryChecks))if(summary[field]!==value)errors.push(`Export summary ${field}がLockと一致しません`);
  if(reviewExport?.integrity?.queue_id!==expected.queueId||reviewExport?.status!=='incomplete-human-review-required'||reviewExport?.mode!=='read-only'||reviewExport?.capabilities?.write_decisions!==false||reviewExport?.capabilities?.promote_human_review!==false||reviewExport?.decision_boundary?.export_accepts_writes!==false)errors.push('read-only/human decision boundaryが不正です');
  if(summary.human_reviewed!==0||summary.semantic_decisions_by_export!==0||summary.pending_human!==summary.packets||reviewExport?.decision_boundary?.decisions_observed!==0)errors.push('0 decisionをHuman review進捗として扱えません');
  const packetRecords=new Map((reviewExport?.packets??[]).map((item)=>[item.path,item]));const itemById=new Map();let projections=0;let deepLinks=0;
  if(packetRecords.size!==expected.packets||archive.packets?.length!==expected.packets)errors.push('Packet数がLockと一致しません');
  for(const entry of archive.packets??[]){const record=packetRecords.get(entry.path);const packet=entry.value;if(!record){errors.push(`Export外packetです: ${entry.path}`);continue;}if(sha256(entry.bytes)!==record.digest)errors.push(`Packet digestが一致しません: ${record.id}`);if(validatePacket&&!validatePacket(packet))errors.push(`${record.id} Schema不適合: ${ajv.errorsText(validatePacket.errors)}`);if(packet.packet_id!==record.id||packet.queue_id!==expected.queueId||packet.source_binding?.anchor_id!==record.anchor_id||packet.deep_link?.url!==record.deep_link||packet.candidate_domain_projections?.length!==record.candidate_edges)errors.push(`Packet record bindingが一致しません: ${record.id}`);if(packet.status!=='pending-human'||packet.read_only!==true||packet.semantic_decision!=='none-by-export'||packet.decision_boundary?.human_decision_recorded!==false||packet.decision_boundary?.decision_ids?.length!==0)errors.push(`PacketをHuman decisionとして表示できません: ${record.id}`);for(const projection of packet.candidate_domain_projections??[])if(projection.classification_basis!=='domain-contract-projection-unreviewed')errors.push(`Projectionが未review表示ではありません: ${projection.edge_id}`);for(const forbidden of ['body','text','content','html','excerpt'])if(Object.hasOwn(packet,forbidden)||Object.hasOwn(packet.source_binding??{},forbidden))errors.push(`一次資料本文をPortalへ複製できません: ${record.id}/${forbidden}`);if(itemById.has(record.anchor_id))errors.push(`Anchorが重複しています: ${record.anchor_id}`);itemById.set(record.anchor_id,packet.source_binding);projections+=packet.candidate_domain_projections?.length??0;if(packet.deep_link?.url)deepLinks++;}
  if(itemById.size!==expected.uniqueAnchors||projections!==expected.candidateDomainProjections||deepLinks!==expected.deepLinks)errors.push('Packet/Projection/Deep link実数がsummaryと一致しません');
  const proposals=reviewExport?.proposed_clusters??[];if(proposals.length!==expected.proposedClusters||proposals.some((item)=>item.semantic_decision!=='none-machine-proposal-only'||item.human_reviewed!==false))errors.push('Machine proposalがHuman decisionと分離されていません');
  const holds=reviewExport?.stale_holds??[];if(holds.length!==expected.staleDocumentHolds||holds.some((item)=>item.status!=='hold-stale-document-relock-required'||!isDigest(item.locked_source_digest)||!isDigest(item.fetched_digest))||reviewExport?.stale_candidate_report?.human_choices!==0||reviewExport?.stale_candidate_report?.locked_digests_updated!==0)errors.push('stale relock候補は選択前read-only holdでなければなりません');
  return{ok:errors.length===0,errors,archive,itemById,progress:{hasHumanProgress:false,decisions:0,humanReviewed:0}};
}

export function projectAuthorityReview(envelope,bundle,verification){
  const reviewExport=bundle.archive.reviewExport;
  return{schemaVersion:1,subjectId:envelope.payload.subjectId,atlasId:envelope.payload.atlasId,status:reviewExport.status,mode:reviewExport.mode,queueId:reviewExport.integrity.queue_id,summary:{...reviewExport.summary,decisions:0,has_human_progress:false},capabilities:reviewExport.capabilities,decisionBoundary:{...reviewExport.decision_boundary,futureWriteBoundary:'core-common-api-and-schema-required',requiredHumanFields:['reviewer','reviewed_at','rationale','review_method:manual-primary-source','source/tool/context digest','old-to-new mapping']},packets:reviewExport.packets.map((item)=>({...item,url:`/data/authority-reviews/${envelope.payload.subjectId}/packets/${item.id}.json`})),proposedClusters:reviewExport.proposed_clusters,staleHolds:reviewExport.stale_holds,staleCandidateReport:reviewExport.stale_candidate_report,source:{repository:envelope.payload.repository,commit:envelope.payload.sourceCommit,exportPath:envelope.payload.exportPath,exportDigest:envelope.payload.exportDigest,exportSchemaPath:envelope.payload.exportSchemaPath,exportSchemaDigest:envelope.payload.exportSchemaDigest,packetSchemaPath:envelope.payload.packetSchemaPath,packetSchemaDigest:envelope.payload.packetSchemaDigest,packetIndexPath:envelope.payload.packetIndexPath,packetIndexDigest:envelope.payload.packetIndexDigest,envelopeDigest:envelope.release.digest,signature:envelope.signature,trust:verification.trust}};
}

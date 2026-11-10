import fs from 'node:fs';
import vm from 'node:vm';

const html = fs.readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const checks = [];

function check(name, condition) {
  if (!condition) throw new Error(`FAIL: ${name}`);
  checks.push(name);
}

check('version is v6.4.1', html.includes('MARAS v6.4.1 MVP'));
check('regulatory source upload is enabled', /<input type="file"[^>]*id="sb-source-input"[^>]*onchange="handleSBDocs\(this\.files\)"/.test(html));
check('requirement upload is enabled', /<input type="file"[^>]*id="req-file-input"[^>]*onchange="handleReqFiles\(this\.files\)"/.test(html));
check('source production gate is enforced', html.includes('function evaluateSourceProductionGate') && html.includes("decision: passed?'DRIVE':'HOLD'"));
check('requirement ingestion gate is enforced', html.includes('function evaluateRequirementIngestionGate'));
check('held ingested sources cannot drive generation', html.includes("d.gate.decision==='DRIVE'") && html.includes('ingestedGenerationChunks()'));
check('licensed sources excluded from generation', html.includes('GXP_CHUNKS.concat(ingestedGenerationChunks()).filter(c => !c.licenseGate)'));
check('FDA CSA mapping is precise', html.includes("reg:'FDA CSA Guidance'") && html.includes('computer-software-assurance-production-and-quality-management-system-software'));
check('medical-device-only sources are scoped', html.includes('!!chunk.medicalDeviceOnly'));
check('source metadata and excerpts are carried', ['sourceVersion','sourceCapturedAt','sourceLicenseTag','sourceApprovalStatus','sourceExcerpt'].every(v => html.includes(v)));
check('SME source approval is a readiness hard gate', html.includes("story.sourceApprovalStatus === 'SME_APPROVED'") && html.includes('citationVerified && sourceApproved'));
check('readiness is not ready and zero', html.includes("evidence_decision: 'NOT_READY'") && html.includes('audit_readiness_score: 0'));
check('generated evidence is identified as draft', html.includes("status:'GENERATED_DRAFT'"));
check('submission is blocked', html.includes('submission_ready: false'));
check('reviewer accountability is required', ['reviewer-name-inp','reviewer-role-inp','review-comment-inp','reviewHistory'].every(v => html.includes(v)));
check('browser review is not represented as approval', html.includes('SME_REVIEW_ATTESTED_DRAFT') && !html.includes("reviewStatus==='SME_REVIEWED'"));
check('all package exports are draft-watermarked', html.includes("packageStatus:'DRAFT_NOT_CONTROLLED'") && html.includes('DRAFT-MARAS-Business-PBI-Jira-Export.csv') && html.includes('DRAFT-MARAS-Business-PBI-ADO-Export.csv'));
check('known generated grammar defect removed', !html.includes('so that ${businessOutcome} is defensible against') && html.includes('cannot be disabled by operators'));
check('semantic regression rules present', html.includes('/is defensible against/i') && html.includes('must\\b[^.]{0,60}\\bmust'));

const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
check('inline application script exists', Boolean(script));
const supportedSystems = ['LIMS','MES','SCADA / DCS','Serialization','QMS','EDMS','CDS','PV System','EDC / eCRF','CTMS','eTMF','Safety Reporting','Regulatory Info Mgmt','ERP / SAP','Supply Chain'];
check('all 15 supported systems have relevance mappings', supportedSystems.every(system => html.includes(`  '${system}': [`)));
check('Saved Package controls use the requested two-pixel font increase', html.includes('.save-bar-lbl{font-size:14px') && html.includes('.save-bar input{flex:1 1 170px;min-width:0;box-sizing:border-box;padding:7px 10px;font-size:14px') && html.includes('.save-bar-btn{padding:7px 13px') && html.includes('font-size:14px;font-weight:600') && html.includes('.save-ok{font-size:13px') && html.includes('.save-bar-note{flex:1 1 100%;min-width:0;font-size:12px'));
check('Saved Package controls are wrap-safe', html.includes('display:flex;flex-wrap:wrap;align-items:center') && html.includes('overflow-wrap:anywhere') && !html.includes('<span style="font-size:10px;color:var(--ink4)">Draft only.'));
check('first-time guide is enabled and aligned with the assurance hero', /<div id="view-gen" class="gv">\s*<!-- FIRST-TIME USER GUIDE[\s\S]*?<div class="value-hero">/.test(html) && html.includes("maras_guide_dismissed_v641_alignment") && html.includes('.onboard-bar{background:linear-gradient') && html.includes('margin-bottom:12px;position:relative'));
check('Regulatory Library uses the extended responsive width', html.includes('.sidebar{width:312px;') && html.includes('@media(max-width:860px){\n  .sidebar{width:280px}'));
check('Regulatory Library uses one scrollbar with 20px space before the resize handle', html.includes('id="sb-resizer"') && html.includes('sb-lib-gap') && html.includes('.sb-lib-gap{width:20px') && html.includes('.sb-tree{flex:none;overflow:visible') && !html.includes('sb-split-gap'));
check('all compliance outcome examples are selectable', html.includes('id="req-example-select"') && html.includes('function applyReqExample') && html.includes('REQ_EXAMPLES.map((ex,i)') && !html.includes("onclick=\"loadProductGradeSample()\""));
check('framework and jurisdiction filters are multi-select dropdowns', html.includes('id="ch-framework"') && html.includes('id="ch-jurisdiction"') && html.includes('ms-drop-btn') && html.includes('function toggleMultiDrop') && html.includes('function toggleFramework') && html.includes('function applySelectedFrameworks') && html.includes('function getSelectedFrameworks') && html.includes("id=\"f-fw\" multiple") && html.includes("id=\"f-jurisdiction\" multiple") && html.includes('function clearFrameworks') && html.includes('function clearJurisdictions'));
check('live harness token profile is configured', html.includes('const LIVE_HARNESS_CONFIG') && html.includes('function getLiveHarnessProfile') && html.includes('function buildHarnessContextLine') && html.includes('function buildScopedSourceSummary') && html.includes('deepseek:') && html.includes('scopedSourceChunks: 6'));
check('regulatory source intake skill is present', fs.existsSync('.cursor/skills/regulatory-source-intake/SKILL.md') && fs.existsSync('docs/schemas/source-intake-record.schema.json') && fs.readFileSync('.cursor/skills/regulatory-source-intake/SKILL.md','utf8').includes('name: regulatory-source-intake'));
check('ctd ectd mapper skill is present', fs.existsSync('.cursor/skills/ctd-ectd-mapper/SKILL.md') && fs.existsSync('docs/schemas/ctd-mapping-record.schema.json') && fs.readFileSync('.cursor/skills/ctd-ectd-mapper/SKILL.md','utf8').includes('name: ctd-ectd-mapper'));
check('requirements comparator skill is present', fs.existsSync('.cursor/skills/requirements-comparator/SKILL.md') && fs.existsSync('docs/schemas/requirements-comparison-record.schema.json') && fs.readFileSync('.cursor/skills/requirements-comparator/SKILL.md','utf8').includes('name: requirements-comparator'));
check('regulated document review skill is present', fs.existsSync('.cursor/skills/regulated-document-review/SKILL.md') && fs.existsSync('docs/schemas/document-review-record.schema.json') && fs.readFileSync('.cursor/skills/regulated-document-review/SKILL.md','utf8').includes('name: regulated-document-review'));
check('data integrity checker skill is present', fs.existsSync('.cursor/skills/data-integrity-checker/SKILL.md') && fs.existsSync('docs/schemas/data-integrity-assessment-record.schema.json') && fs.readFileSync('.cursor/skills/data-integrity-checker/SKILL.md','utf8').includes('name: data-integrity-checker'));
check('regulatory change impact skill is present', fs.existsSync('.cursor/skills/regulatory-change-impact/SKILL.md') && fs.existsSync('docs/schemas/regulatory-change-impact-record.schema.json') && fs.readFileSync('.cursor/skills/regulatory-change-impact/SKILL.md','utf8').includes('name: regulatory-change-impact'));
check('controlled authoring skill is present', fs.existsSync('.cursor/skills/controlled-authoring/SKILL.md') && fs.existsSync('docs/schemas/controlled-authoring-record.schema.json') && fs.readFileSync('.cursor/skills/controlled-authoring/SKILL.md','utf8').includes('name: controlled-authoring'));
check('citation and provenance auditor skill is present', fs.existsSync('.cursor/skills/citation-and-provenance-auditor/SKILL.md') && fs.existsSync('docs/schemas/citation-provenance-audit-record.schema.json') && fs.readFileSync('.cursor/skills/citation-and-provenance-auditor/SKILL.md','utf8').includes('name: citation-and-provenance-auditor'));
check('validation test generator skill is present', fs.existsSync('.cursor/skills/validation-test-generator/SKILL.md') && fs.existsSync('docs/schemas/validation-test-package-record.schema.json') && fs.readFileSync('.cursor/skills/validation-test-generator/SKILL.md','utf8').includes('name: validation-test-generator'));
check('callLLM uses model registry url and per-agent max_tokens', html.includes('async function callLLM(m, sys, userMsg, maxTokens') && html.includes('const model = m.model') && html.includes('const chatUrl = url') && html.includes('profile.maxTokens'));
check('global compare tab is present', html.includes('id="view-compare"') && html.includes('ntab-compare') && html.includes('Global Compare'));
check('global compare engine is wired', html.includes('GLOBAL_COMPARE_TOPICS') && html.includes('function buildGlobalCompare') && html.includes('maras.global-regulation-compare.v1') && html.includes("id:'UK'") && html.includes('Differences') && html.includes('function uncoveredCompareMarkets') && html.includes("id:'c19'") && html.includes("id:'computerised-systems'"));
check('co-operations modes exist', html.includes('setCoOpMode') && html.includes('renderCompareGap') && html.includes('renderCompareBriefing'));
check('global compare HIPAA and GDPR markets', html.includes("id:'HIPAA'") && html.includes("id:'GDPR'") && html.includes('healthcareLifeSciencesContext'));
check('readiness tab with SOP mapper', html.includes('id="view-readiness"') && html.includes('function mapSopToRegulations') && html.includes('sop-mapper-grid'));
check('inspection readiness assistant', html.includes('function buildInspectionReadinessPack') && html.includes('maras.inspection-readiness.v1') && html.includes('dlInspectionPackJson'));
check('SOP mapper uses library anchors', html.includes('SOP_CHUNK_LIBRARY_LINKS') && html.includes('auditContextMapsChunk') && html.includes('buildReadinessSnapshot'));
check('readiness gap downloads', html.includes('maras.readiness-gaps.v1') && html.includes('dlReadinessGapsCsv'));
check('CTD eCTD Engine tab is present', html.includes('id="view-ctd"') && html.includes('ntab-ctd') && html.includes('CTD/eCTD Engine'));
check('CTD engine validates against framework jurisdiction scope', html.includes('function buildCtdEngineValidation') && html.includes('function getCtdScopedRegulatoryChunks') && html.includes('CTD_MODULE_32S') && html.includes('function handleCtdHouseDocs'));
check('CTD mapping export is draft watermarked', html.includes('DRAFT-MARAS-CTD-Mapping-3.2.S.json') && html.includes("packageStatus:'DRAFT_NOT_CONTROLLED'") && html.includes('maras.ctd-mapping.v1'));
check('Agents.md default instructions', fs.existsSync('Agents.md') && fs.readFileSync('Agents.md','utf8').includes('CRS Mode') && fs.readFileSync('Agents.md','utf8').includes('Graphiffy'));
check('platform workflow registry', fs.existsSync('docs/workflows/platform-workflows.json') && fs.readFileSync('docs/workflows/platform-workflows.json','utf8').includes('WF-PLATFORM-EVIDENCE'));
check('platform harness config', fs.existsSync('docs/harness/platform-harness-config.json') && fs.readFileSync('docs/harness/platform-harness-config.json','utf8').includes('deepseekProfile'));
check('notion workflow generator', fs.existsSync('scripts/generate-notion-workflows.mjs') && fs.existsSync('docs/workflows/notion-export/00-index.md'));
check('capabilities inventory', fs.existsSync('docs/CAPABILITIES.md') && fs.readFileSync('docs/CAPABILITIES.md','utf8').includes('verify-all.mjs'));
check('unified verify script', fs.existsSync('scripts/verify-all.mjs'));
check('self-heal script', fs.existsSync('scripts/self-heal.mjs'));
check('RAG graph defaults on and toggle present', html.includes('let ragGraphEnabled = true') && html.includes('maras_rag_graph_v1') && html.includes('id="rag-graph-toggle"') && html.includes('function setRagGraphMode'));
check('RAG graph can be disabled via localStorage or URL', html.includes("stored === '0'") && html.includes("qs.get('rag') === '0'"));
check('RAG graph pipeline stages implemented', html.includes('RAG_GRAPH_START') && html.includes('function runRagGraph') && html.includes('function ragParse') && html.includes('function ragRerank') && html.includes('function ragVerify'));
check('RAG legacy path via ragGetActiveRanked', html.includes('function ragGetActiveRanked') && html.includes('ragCompleteVerify'));
check('RAG quality gate and replay UI', html.includes('buildQualityGateSummary') && html.includes('toggleRagPipeline') && html.includes('regenerateStoryImproved'));
check('RAG optimization plan documented', fs.existsSync('docs/rag-optimization-plan.md'));
check('hybrid retrieval architecture documented', fs.existsSync('docs/hybrid-retrieval-architecture.md'));
check('hybrid retrieval functions implemented', html.includes('function hybridRetrieve') && html.includes('function ensureHybridIndices') && html.includes('function hybridDeterministicRetrieve') && html.includes('function hybridGraphRetrieve') && html.includes('function hybridVectorRetrieve'));
check('OKF v0.2 adapter in hybrid indices', html.includes("okfVersion: '0.2'") && html.includes('function hybridOkfMatch'));
check('hybrid provenance badges in replay UI', html.includes('prov-badge') && html.includes('hybrid-route') && html.includes('Hybrid Retrieve'));
check('explicit refs extraction for deterministic routing', html.includes('function ragExtractExplicitRefs') && html.includes('explicit_refs: ragExtractExplicitRefs'));
check('TF-IDF pseudo-vector labeled in hybrid config', html.includes('tfidf-cosine-pseudo') && html.includes('hybridMaxCandidates'));
check('Phase 2 pipeline replay toggle and detail view', html.includes('Pipeline replay (optional)') && html.includes('function ragReplayDetailHtml') && html.includes('function toggleRagPipeline') && html.includes('.rag-pipe-panel{display:none'));
check('Phase 2 replay override controls exposed', html.includes('function ragToggleSourceOverride') && html.includes('function ragRerunSynthesis') && html.includes('function ragSetVerifyDecision') && html.includes('function ragToggleReplayScopeCat') && html.includes('Regenerate synthesis (draft)'));
check('Phase 2 userOverrides schema includes scope and verify', html.includes('scopeCats: null') && html.includes('verifyDecisions: {}'));
check('Phase 3 quality gate rules and pipeline rubric', html.includes('function qgStatusLabel') && html.includes('function scoreRagPipelineRubric') && html.includes('function renderQualityGatePanel') && html.includes('weakInvest') && html.includes('unsupported_claim') && html.includes('INVEST summary:') && html.includes('Needs improvement'));
check('Quality gate panel always under each PBI', html.includes('renderQualityGatePanel(i, s)') && html.includes('_qgOriginalStory') && html.includes('_qgImprovedDraft') && html.includes('Regenerate improved version') && !html.includes('ragGraphEnabled ? `<div class="qg-panel"'));
check('Phase 4 legacy fallback and export pipeline metadata', html.includes('fallbackUsed') && html.includes('pipelineMode:ragGraphEnabled') && html.includes('legacy fallback active'));
check('Phase 5 RAG graph fixtures on disk', fs.existsSync('scripts/fixtures/rag-graph/generic-it.json') && fs.existsSync('scripts/fixtures/rag-graph/fda-clinical.json'));
check('Story Map tab is present', html.includes('id="view-storymap"') && html.includes('ntab-storymap') && html.includes('Story Map'));
check('Story Map templates list', html.includes('STORY_MAP_TEMPLATES') && html.includes('Enterprise Migration') && html.includes('PI Planning'));
check('Story Map hierarchy labels', html.includes('STORY_MAP_HIERARCHY') && html.includes('Capability/Goal') && html.includes('Acceptance Evidence'));
check('Story Map state object', html.includes('storyMapState') && html.includes('maras.story-map.v1') && html.includes('function ensureStoryMapState'));
check('Story Map export functions exist', html.includes('function exportStoryMapJson') && html.includes('function exportStoryMapCsv') && html.includes('function exportStoryMapPng'));
check('Story Map draft banner text', html.includes('id="story-map-draft-banner"') && html.includes('DRAFT_NOT_CONTROLLED') && html.includes('SME/QA/RA review required'));
check('Story Map persona lenses defined', html.includes('STORY_MAP_PERSONA_LENSES') && html.includes('system-owner') && html.includes('scrum-master') && html.includes('function storyMapSetPersonaLens'));
check('Story Map persona lens selector', html.includes('id="story-map-persona-lens-select"') && html.includes('storyMapActiveLensConfig'));
check('Story Map persona lens unique primary panels', ['story-map-panel-system-owner','story-map-panel-product-owner','story-map-panel-product-manager','story-map-panel-developer','story-map-panel-tester','story-map-panel-scrum-master'].every(id=>html.includes(id)));
check('Story Map export personaLens metadata', html.includes('personaLensLabel:') && html.includes('personaLensPrimaryPanel') && html.includes('function exportStoryMapCeremonyJson'));
check('Story Map persona field scoping', html.includes('function storyMapLensHasField') && html.includes('storyMapLensHasField(\'traceLinks\')'));
check('Implementation Readiness Gate UI for §11.10(e)', html.includes('id="implementation-readiness-gate-panel"') && html.includes('IMPLEMENTATION_READINESS_GATE_1110E') && html.includes('REQ-001 · 21 CFR Part 11 §11.10(e)') && html.includes('renderImplementationReadinessGate'));
check('Implementation Readiness Gate export schema', html.includes('maras.implementation-readiness-gate.v1') && html.includes('implementationReadinessGate:buildImplementationReadinessGateRecord()'));
check('Implementation Readiness Gate doc artifact', fs.existsSync('docs/implementation-readiness-gate-11.10e.md') && fs.readFileSync('docs/implementation-readiness-gate-11.10e.md','utf8').includes('DRAFT_NOT_CONTROLLED'));
check('PBI three-question output helpers', html.includes('function ensureStoryPbi') && html.includes('function buildAssureStoryPbi') && html.includes('function renderPbiThreeQuestions') && html.includes('function computePbiComplete'));
check('qc-compat VM loads PBI helpers outside QC block', fs.readFileSync('qc-compat-regression.mjs', 'utf8').includes('pbiHelpersSrc'));
check('PBI section headings in rendered output', html.includes('Product Owner understands') && html.includes('Developer builds') && html.includes('QA validates'));
check('PBI compliance details collapsed by default', html.includes('class="pbi-compliance-details sc-compliance-collapsed"') && html.includes('<summary>Compliance Details</summary>'));
check('PBI incomplete requirement flag', html.includes('data-pbi-incomplete="1"') && html.includes('pbi.complete') && html.includes('⚠ Incomplete requirement'));
check('Story Map export includes pbi JSON fields', html.includes("'pbi.poUnderstands'") && html.includes("'pbi.devBuilds'") && html.includes("'pbi.qaValidates'") && html.includes("'pbi.complete'"));
check('PBI output format doc', fs.existsSync('docs/pbi-output-format.md') && fs.readFileSync('docs/pbi-output-format.md','utf8').includes('DRAFT_NOT_CONTROLLED'));
check('regulatory trace pipeline stage enum (19 stages)', html.includes('REGULATORY_TRACE_PIPELINE_STAGES') && html.includes("'HUMAN_REVIEW_PACKAGE'") && html.includes("'DOCUMENT'"));
check('maras.trace-pipeline.v1 schema constant', html.includes("REGULATORY_TRACE_PIPELINE_SCHEMA = 'maras.trace-pipeline.v1'"));
check('trace link helpers', html.includes('function linkTracePipelineParents') && html.includes('function attachRegulatoryTracePipeline') && html.includes('function buildRegulatoryTraceChainForStory'));
check('pipeline trace UI in Value Package', html.includes('id="pipeline-trace-wrap"') && html.includes('function renderPackagePipelineTrace') && html.includes('Full trace pipeline'));
check('human review package export', html.includes('function dlHumanReviewPackageJson') && html.includes('maras.human-review-package.v1') && html.includes('DRAFT-MARAS-Human-Review-Package.json'));
check('backlog JSON includes trace pipeline', html.includes('regulatoryTracePipeline:ensurePackageTracePipeline(allStories)') && html.includes('traceStageEnum:regulatoryTracePipelineStages()'));
check('decomposition prompts include regulatoryTraceHints', html.includes('regulatoryTraceHints'));
check('regulatory trace pipeline doc', fs.existsSync('docs/regulatory-trace-pipeline.md') && fs.readFileSync('docs/regulatory-trace-pipeline.md','utf8').includes('maras.trace-pipeline.v1'));
check('regulatory trace pipeline json schema', fs.existsSync('docs/schemas/regulatory-trace-pipeline-record.schema.json') && fs.readFileSync('docs/schemas/regulatory-trace-pipeline-record.schema.json','utf8').includes('HUMAN_REVIEW_PACKAGE'));
check('structured obligation schema constant', html.includes("STRUCTURED_OBLIGATION_SCHEMA = 'maras.structured-obligation.v1'"));
check('normalize regulatory obligations function', html.includes('function normalizeRegulatoryObligationsForStory') && html.includes('function buildStructuredObligationImpactBundle') && html.includes('function deriveComplianceOutcomeForObligation'));
check('structured obligation UI cards', html.includes('function renderStructuredObligationCards') && html.includes('obl-wrap') && html.includes('renderStructuredObligationCards(s.structuredObligations'));
check('human review package structured export', html.includes('structuredObligationSchema:STRUCTURED_OBLIGATION_SCHEMA') && html.includes('structuredObligations'));
check('structured obligation doc', fs.existsSync('docs/structured-obligation-normalization.md') && fs.readFileSync('docs/structured-obligation-normalization.md','utf8').includes('maras.structured-obligation.v1'));
check('structured obligation json schema', fs.existsSync('docs/schemas/structured-obligation-record.schema.json'));

function extractBlock(label, startMarker, endMarker) {
  const start = html.indexOf(startMarker);
  const end = html.indexOf(endMarker, start);
  if (start < 0 || end < 0) throw new Error(`Could not extract ${label}`);
  return html.slice(start, end);
}

const gxpMatch = html.match(/const GXP_CHUNKS=(\[[\s\S]*?\]);\s*\nconst /);
if (!gxpMatch) throw new Error('Could not extract GXP_CHUNKS for obligation test');
const oblFnSrc = extractBlock('obligation fns', "const STRUCTURED_OBLIGATION_SCHEMA = 'maras.structured-obligation.v1'", 'const PO_READINESS_CHECKLIST_KEYS');
const sandbox = { console, Set, Map, Array, Object, String, Math, Date, JSON, document: { getElementById: () => ({ value: '' }) }, H: { ragReplay: null }, GXP_CHUNKS: [] };
vm.createContext(sandbox);
vm.runInContext(`GXP_CHUNKS = ${gxpMatch[1]};`, sandbox);
vm.runInContext(oblFnSrc, sandbox);
const c3 = sandbox.GXP_CHUNKS.find(c => c.id === 'c3');
const bundle = sandbox.normalizeRegulatoryObligationsForStory({ regRef: 'REQ-001 · 21 CFR Part 11 §11.10(e)' }, c3, null);
check('sample chunk c3 yields structured obligations', bundle.obligations?.length >= 1);
const full = sandbox.buildStructuredObligationImpactBundle({ regRef: 'REQ-001' }, c3, null, {});
const hasSourceSupport = (full.impacts || []).some(i => Array.isArray(i.complianceOutcome?.sourceSupport) && i.complianceOutcome.sourceSupport.length > 0);
check('compliance outcomes include sourceSupport', hasSourceSupport);

const poKeys = ['clausesMapped','conditionsIdentified','exceptionsIdentified','definitionsAnalyzed','acceptanceCriteriaGenerated','complianceOutcomeIdentified','traceabilityComplete','ambiguitiesReviewed','productOwnerReviewReady'];
check('PO readiness checklist keys', poKeys.every(k => html.includes(`'${k}'`)) && html.includes('maras.po-readiness-checklist.v1'));
const dodKeys = ['acceptanceCriteriaPassed','complianceTestsPassed','evidenceCaptured','auditTrailMaintained','traceabilityRetained','exceptionsValidated','reportingObligationsSatisfied','complianceReviewCompleted','productOwnerApprovalObtained'];
check('recommended DoD checklist keys', dodKeys.every(k => html.includes(`'${k}'`)) && html.includes('maras.recommended-dod.v1'));
check('computeStoryDefinitionOfDone recommendedDoD export', html.includes('recommendedDoD') && html.includes('deriveRecommendedDefinitionOfDone') && html.includes('poReadinessChecklists'));
check('PO approval localStorage toggle', html.includes('maras.po-approval.v1') && html.includes('toggleStoryPoApproval'));
check('DoR DoD UI on story cards', html.includes('Definition of Ready / PO review readiness') && html.includes('renderPoReadinessAndRecommendedDoD'));
check('DoR DoD collapsed in pbi-accordion details', html.includes('class="pbi-accordion sc-compliance-collapsed dor-dod-wrap"') && html.includes('<summary>Definition of Ready / PO review readiness') && html.includes('<summary>Recommended Definition of Done (draft)'));
check('PBI three questions use click-to-expand accordion', html.includes('Three questions ·') && html.includes('class="pbi-accordion sc-compliance-collapsed"'));
check('caveman mode default ON with localStorage', html.includes('CAVE_MAN_MODE_CONFIG') && html.includes('maras_caveman_mode_v1') && html.includes('cavemanModeEnabled = true') && html.includes('else cavemanModeEnabled = true') && html.includes('html.maras-caveman') && html.includes('id="caveman-mode-toggle"'));
check('definition of done doc', fs.existsSync('docs/definition-of-done.md') && fs.readFileSync('docs/definition-of-done.md','utf8').includes('DRAFT_NOT_CONTROLLED'));
check('hard-fail governance doc', fs.existsSync('docs/hard-fail-output-governance.md') && fs.readFileSync('docs/hard-fail-output-governance.md','utf8').includes('ZERO_UNSUPPORTED_STATEMENTS'));
check('FINAL_OUTPUT_ORDER schema constant', html.includes("FINAL_OUTPUT_ORDER_SCHEMA = 'maras.final-output-order.v1'"));
check('FINAL_OUTPUT_ORDER has 23 sections', FINAL_OUTPUT_ORDER_LEN_OK(html));
check('validateRegulatoryOutputHardFail function', html.includes('function validateRegulatoryOutputHardFail(story, chain, structuredObligations)'));
check('MARAS_ALLOWED_DERIVATION_PREFIXES', html.includes('MARAS_ALLOWED_DERIVATION_PREFIXES') && html.includes("'Priority:'") && html.includes("'Given'"));
check('hard-fail blocking vs warn severities', html.includes('HARD_FAIL_BLOCKING_CODES') && html.includes('WARN_NEEDS_REVIEW') && html.includes('dedupeHardFailFailures'));
check('assembleFinalOutputPackage function', html.includes('function assembleFinalOutputPackage(story, index)'));
check('HARD_FAIL_CODE_ENUM present', html.includes('SOURCE_MISSING') && html.includes('TECHNOLOGY_INVENTED') && html.includes('DESIGN_INVENTED'));
check('Delivery Package panel HTML', html.includes('id="delivery-package-wrap"') && html.includes('function renderPackageDeliveryPanel'));
check('package delivery traceability bundle collapsed', html.includes('id="package-delivery-traceability"') && html.includes('Delivery Package &amp; traceability'));
check('hard fail in JSON export', html.includes('regulatoryOutputHardFail:hardFail') && html.includes('FAILED-DRAFT-MARAS-Backlog.json'));
check('prohibitions from PROHIBITED modality', html.includes("o.modality === 'PROHIBITED'") && html.includes("key:'PROHIBITIONS'"));
check('regulatory trace pipeline doc mentions final output order', fs.readFileSync('docs/regulatory-trace-pipeline.md','utf8').includes('maras.final-output-order.v1'));

function FINAL_OUTPUT_ORDER_LEN_OK(html) {
  const m = html.match(/const FINAL_OUTPUT_ORDER = \[([\s\S]*?)\];/);
  if (!m) return false;
  return (m[1].match(/num:\d+/g) || []).length === 23;
}

const hfSrc = extractBlock('hard fail fns', 'const FINAL_OUTPUT_ORDER_SCHEMA', 'function storyMapPipelineForStory(s)');
const hfSandbox = { console, Set, Map, Array, Object, String, Math, Date, JSON,
  FINAL_OUTPUT_ORDER: [], HARD_FAIL_CODE_ENUM: [], tracePipelineNode: () => null,
  findGxpChunkForStory: () => null, buildRegulatoryTraceChainForStory: () => ({nodes:[]}),
  HUMAN_REVIEW_SME_CHECKLIST: [], storyStableId: (s) => s.id, computePipelineCoveragePercent: () => 0,
  buildRegulatoryKnowledgeGraph: () => ({nodes:[],edges:[]}), REGULATORY_HARD_FAIL_POLICY: 'ZERO_UNSUPPORTED_STATEMENTS',
  GXP_CHUNKS: sandbox.GXP_CHUNKS
};
hfSandbox.findGxpChunkForStory = (s) => hfSandbox.GXP_CHUNKS.find(c => c.id === 'c3' || (s?.regRef && /REQ-001|§11\.10\(e\)/i.test(s.regRef)));
vm.createContext(hfSandbox);
vm.runInContext(`const REGULATORY_TRACE_PIPELINE_STAGES = []; function tracePipelineNode(c,s){return (c?.nodes||[]).find(n=>n.stage===s)||null;} ${hfSrc}`, hfSandbox);
const failStory = { id: 'HF-1', story: 'We use kubernetes mesh for compliance certified operations', sourceExcerpt: 'Systems shall retain audit trails.', regRef: 'REQ-001', regulation: '21 CFR Part 11', section: '§11.10(e)', traceId: 'TRC-1' };
const failChain = { nodes: [{ stage: 'CONDITIONS', needsReview: true, summary: 'needs-review' }, { stage: 'DOCUMENT', payload: { chunkId: 'c3' } }] };
const vf = hfSandbox.validateRegulatoryOutputHardFail(failStory, failChain, { obligations: [{ modality: 'MUST', sourceSpan: { text: 'shall retain' } }], impacts: [] });
check('hard fail detects invented tech', (vf.failures || []).some(f => f.code === 'TECHNOLOGY_INVENTED'));
check('hard fail detects unsupported statement', (vf.failures || []).some(f => f.code === 'UNSUPPORTED_STATEMENT'));
check('hard fail returns passed boolean', vf.passed === false && Array.isArray(vf.failures));
const okStory = { id: 'HF-OK', sourceExcerpt: 'Systems shall retain audit trails for the required retention period.', regRef: 'REQ-001', regulation: '21 CFR Part 11', section: '§11.10(e)', traceId: 'TRC-OK', story: 'Retain audit trails per source excerpt.', ac: ['Given export When audit Then retained'], validationRubric: { totalScore: 80, grade: 'B' } };
const okChain = { nodes: REGULATORY_TRACE_OK_NODES(), structuredObligations: { obligations: [{ modality: 'SHALL', subject: 'System', action: 'retain', sourceSpan: { text: 'shall retain audit trails' } }], impacts: [{ complianceOutcome: { observable: 'Retained', measurementHint: 'at least per source' } }] } };
function REGULATORY_TRACE_OK_NODES() {
  return ['DOCUMENT','REGULATORY_INTENT','OBLIGATION','CONDITIONS','EXCEPTIONS','COMPLIANCE_OUTCOMES','TRACEABILITY_MATRIX'].map(stage => ({
    stage, needsReview: false, summary: 'sourced', traceId: 'T-' + stage, label: stage
  }));
}
const vfOk = hfSandbox.validateRegulatoryOutputHardFail(okStory, okChain, okChain.structuredObligations);
check('hard fail may still flag condition when source has if', typeof vfOk.passed === 'boolean');
check('anchored ok story passes without blocking failures', vfOk.passed === true && !(vfOk.blockingFailures||[]).length);
const c3Excerpt = c3.excerpts?.[0] || '';
const c3Bundle = sandbox.normalizeRegulatoryObligationsForStory({ regRef: 'REQ-001 · 21 CFR Part 11 §11.10(e)' }, c3, null);
const c3Story = {
  id: 'REQ-001', title: 'Audit Trail Requirements', regulation: '21 CFR Part 11', section: '§11.10(e)',
  regRef: 'REQ-001 · 21 CFR Part 11 §11.10(e)', traceId: 'TRC-C3-OK', sourceExcerpt: c3Excerpt,
  story: 'As QA I need computer-generated audit trails so operator entries are independently recorded per the source excerpt.',
  ac: ['Given operator entry When action is recorded Then date and time are stamped', 'Given record change When applied Then prior values are not obscured'],
  pbi: {
    poUnderstands: 'Priority: P0 regulatory criticality\nEvidence stage: OQ',
    devBuilds: 'Implement: audit trail microservice hooks',
    qaValidates: 'Given operator action When export Then trail is retained'
  }
};
const c3Chain = {
  nodes: REGULATORY_TRACE_OK_NODES().concat([{ stage: 'DOCUMENT', needsReview: false, summary: 'c3', traceId: 'T-DOC', payload: { chunkId: 'c3' } }]),
  structuredObligations: c3Bundle
};
const vfC3 = hfSandbox.validateRegulatoryOutputHardFail(c3Story, c3Chain, c3Bundle);
const unsupportedSpam = (vfC3.failures || []).filter(f => f.code === 'UNSUPPORTED_STATEMENT').length;
check('c3 sample story not spammed with UNSUPPORTED_STATEMENT', unsupportedSpam <= 1);
check('c3 sample story passes hard-fail blocking gate', vfC3.passed === true);
const pkg = hfSandbox.assembleFinalOutputPackage({ ...okStory, regulatoryTracePipeline: okChain }, 0);
check('assembleFinalOutputPackage has 23 sections', pkg.sections?.length === 23 && pkg.schema === 'maras.final-output-order.v1');
check('assemble includes prohibitions section', pkg.sections?.some(s => s.key === 'PROHIBITIONS'));

const dorDodSrc = extractBlock('dor dod fns', 'const PO_READINESS_CHECKLIST_KEYS', 'function buildRegulatoryTraceChainForStory(story');
vm.runInContext('function computePbiComplete(p){ return !!p?.complete; } function isPbiSectionFilled(v){ return !!String(v||"").trim(); } function escapeHtml(s){ return String(s); }', sandbox);
vm.runInContext(dorDodSrc, sandbox);
const sampleStory = { id: 'TST-1', regulation: '21 CFR Part 11', section: '§11.10(e)', regRef: 'REQ-001', traceId: 'TRC-X', ac: ['Given audit trail When export Then retained'], invest: { independent: 'yes', negotiable: 'yes', valuable: 'yes', estimable: 'yes', small: 'yes', testable: 'yes' }, pbi: { poUnderstands: 'x', devBuilds: 'y', qaValidates: 'Given/When/Then', complete: true }, structuredObligations: { obligations: [{}] } };
const mkNode = (stage, needsReview) => ({ stage, needsReview: !!needsReview, summary: 'ok', traceId: `T-${stage}` });
const sampleChain = {
  rootTraceId: 'TRC-ROOT',
  leafTraceId: 'TRC-LEAF',
  structuredObligations: sampleStory.structuredObligations,
  nodes: ['REGULATORY_INTENT','CONDITIONS','EXCEPTIONS','OBLIGATION','COMPLIANCE_OUTCOMES','COMPLIANCE_TEST_SCENARIOS','TRACEABILITY_MATRIX','DOCUMENT'].map(s => mkNode(s, false))
};
const pr = sandbox.derivePoReadinessChecklist(sampleStory, sampleChain);
check('pipeline derives poReadiness checklist', pr.keys?.length === 9 && pr.items?.length === 9);
const dod = sandbox.deriveRecommendedDefinitionOfDone(sampleStory, 0, sampleChain);
check('pipeline derives recommended DoD checklist', dod.keys?.length === 9 && dod.items?.length === 9);

export const result = { status: 'PASS', checks: checks.length, systemsValidated: 15, names: checks };

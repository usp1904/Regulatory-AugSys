import fs from 'node:fs';

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

export const result = { status: 'PASS', checks: checks.length, systemsValidated: 15, names: checks };

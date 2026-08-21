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
check('Regulatory Library uses the extended responsive width', html.includes('.sidebar{width:280px;') && html.includes('@media(max-width:860px){\n  .sidebar{width:232px}'));
check('global compare tab is present', html.includes('id="view-compare"') && html.includes('ntab-compare') && html.includes('Global Compare'));
check('global compare engine is wired', html.includes('GLOBAL_COMPARE_TOPICS') && html.includes('function buildGlobalCompare') && html.includes('maras.global-regulation-compare.v1'));
check('co-operations modes exist', html.includes('setCoOpMode') && html.includes('renderCompareGap') && html.includes('renderCompareBriefing'));
check('readiness tab with SOP mapper', html.includes('id="view-readiness"') && html.includes('function mapSopToRegulations') && html.includes('sop-mapper-grid'));
check('inspection readiness assistant', html.includes('function buildInspectionReadinessPack') && html.includes('maras.inspection-readiness.v1') && html.includes('dlInspectionPackJson'));
check('SOP mapper uses library anchors', html.includes('SOP_CHUNK_LIBRARY_LINKS') && html.includes('auditContextMapsChunk') && html.includes('buildReadinessSnapshot'));
check('readiness gap downloads', html.includes('maras.readiness-gaps.v1') && html.includes('dlReadinessGapsCsv'));
check('Agents.md default instructions', fs.existsSync('Agents.md') && fs.readFileSync('Agents.md','utf8').includes('CRS Mode') && fs.readFileSync('Agents.md','utf8').includes('Graphiffy'));

export const result = { status: 'PASS', checks: checks.length, systemsValidated: 15, names: checks };

import fs from 'node:fs';

const html = fs.readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const checks = [];

function check(name, condition) {
  if (!condition) throw new Error(`FAIL: ${name}`);
  checks.push(name);
}

check('version is v6.4.1', html.includes('MARAS v6.4.1 MVP'));
check('regulatory upload is disabled', /<input type="file"[^>]+disabled aria-disabled="true">[\s\S]{0,250}Controlled source ingestion/.test(html));
check('requirement upload is disabled', /<input type="file"[^>]+disabled aria-disabled="true">[\s\S]{0,250}Requirement-file ingestion/.test(html));
check('no active fake-upload handlers', !html.includes('onchange="handleSBDocs(this.files)"') && !html.includes('onchange="handleReqFiles(this.files)"'));
check('licensed sources excluded from generation', html.includes('GXP_CHUNKS.filter(c => !c.licenseGate)'));
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

export const result = { status: 'PASS', checks: checks.length, systemsValidated: 15, names: checks };

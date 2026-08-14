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

export const result = { status: 'PASS', checks: checks.length, names: checks };

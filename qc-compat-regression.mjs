/**
 * Non-browser regression checks for MARAS QC compatibility.
 * Ensures QC controls do not empty the corpus or drop legacy story fields.
 */
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const html = fs.readFileSync(new URL('./index.html', import.meta.url), 'utf8');

function extract(re, label) {
  const m = html.match(re);
  if (!m) throw new Error(`Could not extract ${label}`);
  return m[1];
}

const gxpChunksSrc = extract(/const GXP_CHUNKS=(\[[\s\S]*?\]);\s*\nconst /, 'GXP_CHUNKS');
const controlledSourcesSrc = extract(/const CONTROLLED_SOURCES=(\{[\s\S]*?\});\s*\n\nconst SOURCE_TRUST/, 'CONTROLLED_SOURCES');
const treeDataSrc = extract(/const TREE_DATA=(\[[\s\S]*?\]);\s*\n/, 'TREE_DATA');

const qcStart = html.indexOf('const QC_CONFIG = {');
const qcEnd = html.indexOf('/* ─── AUTO PREFIX');
if (qcStart < 0 || qcEnd < 0) throw new Error('QC block bounds not found');
const qcSrc = html.slice(qcStart, qcEnd);

const sm = html.match(/function sourceMetaFor\(reg,sourceKey\)\{[\s\S]*?\n\}/);
if (!sm) throw new Error('sourceMetaFor not found');

function makeDom(values = {}) {
  const store = {
    'f-fw': values.fw ?? '',
    'f-system': values.system ?? '',
    'f-client-region': values.region ?? '',
    'f-jurisdiction': values.region ?? '',
    'f-org': values.org ?? '',
    'f-proj': values.proj ?? '',
    'f-outcome': values.outcome ?? '',
  };
  return {
    getElementById(id) {
      return { value: store[id] ?? '', textContent: '', className: '', style: {}, innerHTML: '' };
    }
  };
}

function boot(values = {}, cats = [], items = []) {
  const sandbox = {
    console,
    Set, Map, Array, Object, String, Math, Date, JSON, Number, Boolean, URL, TextDecoder,
    document: makeDom(values),
    selCatsSet: new Set(cats),
    selItems: new Set(items),
    selDomain: values.domain ?? '',
    demoMode: true,
    TREE_DATA: [],
    GXP_CHUNKS: [],
    CONTROLLED_SOURCES: {},
    sbDocs: [],
    reqFiles: [],
    allStories: [],
    H: { stories: [], review: {}, evidence: {}, qcReport: null },
    INGESTED_SOURCE_META: {},
  };
  vm.createContext(sandbox);
  vm.runInContext(`TREE_DATA = ${treeDataSrc};`, sandbox);
  vm.runInContext(`GXP_CHUNKS = ${gxpChunksSrc};`, sandbox);
  vm.runInContext(`CONTROLLED_SOURCES = ${controlledSourcesSrc};`, sandbox);
  vm.runInContext(qcSrc, sandbox);
  vm.runInContext(sm[0], sandbox);
  vm.runInContext(`function autoPrefix(){ return 'GXP'; }`, sandbox);
  const cmpDataStart = html.indexOf('const COMPARE_MARKETS');
  const cmpDataEnd = html.indexOf('/* ─── STATE ─────────────────────────────────────────────────────── */');
  const cmpFnStart = html.indexOf('/* GLOBAL COMPARE ENGINE */');
  const cmpFnEnd = html.indexOf('function dlCompareJson');
  if (cmpDataStart < 0 || cmpDataEnd < 0 || cmpFnStart < 0 || cmpFnEnd < 0) throw new Error('compare block bounds not found');
  vm.runInContext(html.slice(cmpDataStart, cmpDataEnd), sandbox);
  vm.runInContext(html.slice(cmpFnStart, cmpFnEnd), sandbox);
  sandbox.compareMarketSel = new Set(['US', 'EU', 'INT']);
  sandbox.coOpMode = 'matrix';
  const rdStart = html.indexOf('/* READINESS — SOP mapper');
  const rdEnd = html.indexOf('/* ASSURANCE */', rdStart);
  if (rdStart >= 0 && rdEnd > rdStart) vm.runInContext(html.slice(rdStart, rdEnd), sandbox);
  sandbox.QC_CONFIG = vm.runInContext('QC_CONFIG', sandbox);
  sandbox.FDA_CLINICAL_DATA_SCHEMA = vm.runInContext('FDA_CLINICAL_DATA_SCHEMA', sandbox);
  return sandbox;
}

function mainStyleRank(chunks, req, activeCats, treeCats) {
  const qt = (req || '').toLowerCase();
  return chunks.filter(c => {
    if (c.licenseGate) return false;
    if (activeCats && !activeCats.has(c.cat)) return false;
    if (treeCats && !treeCats.has(c.cat)) return false;
    return true;
  }).sort((a, b) => {
    const sa = (a.kws||[]).filter(k => qt.includes(k)).length + (qt.includes(a.reg.toLowerCase()) ? 3 : 0);
    const sb = (b.kws||[]).filter(k => qt.includes(k)).length + (qt.includes(b.reg.toLowerCase()) ? 3 : 0);
    return sb - sa;
  });
}

const failures = [];
function check(name, fn) {
  try { fn(); }
  catch (e) { failures.push(name + ': ' + (e.stack || e.message)); }
}

check('empty-fw keeps a non-empty safe subset', () => {
  const s = boot({});
  const ranked = s.rankChunks('audit trail LIMS Part 11');
  const main = mainStyleRank(s.GXP_CHUNKS, 'audit trail LIMS Part 11', null, null);
  assert.ok(ranked.length > 0, 'safe ranking returned an empty corpus');
  assert.ok(ranked.length <= main.length, 'safe ranking expanded beyond the source corpus');
  assert.ok(ranked._scope, 'rank meta attached');
  assert.ok(ranked.every(c => !c.licenseGate), 'licensed source leaked into generation');
});

check('category scope matches main filter', () => {
  const cats = ['B','C','F'];
  const s = boot({ fw: 'FDA', system: 'LIMS', domain: 'Pharma Mfg' }, cats);
  const ranked = s.rankChunks('audit trail e-signature validation');
  const main = mainStyleRank(s.GXP_CHUNKS, 'audit trail e-signature validation', new Set(cats), null);
  assert.ok(ranked.length > 0);
  ranked.forEach(c => assert.ok(cats.includes(c.cat), 'out of scope cat ' + c.cat));
  assert.ok(ranked.length <= main.length);
  const mainIds = new Set(main.map(c => c.id));
  ranked.forEach(c => assert.ok(mainIds.has(c.id)));
  assert.ok(ranked.every(c => !c.medicalDeviceOnly), 'medical-device-only source leaked into Pharma scope');
});

check('FDA jurisdiction filters EU when US alternatives exist', () => {
  const s = boot({ fw: 'FDA', system: 'LIMS', region: 'United States', domain: 'Pharma Mfg' });
  const ranked = s.rankChunks('21 CFR Part 11 audit trail');
  assert.ok(ranked.length > 0);
  const eu = ranked.filter(c => (c.reg||'').includes('EU GMP'));
  assert.equal(eu.length, 0, 'EU sources should be hard-filtered under FDA when US alternatives exist');
  assert.ok((ranked._jurisdictionSuppressed || []).length >= 1);
  assert.ok(ranked.some(c => (c.reg||'').includes('21 CFR')));
});

check('nation normalization for GDPR under EMA', () => {
  const s = boot({ fw: 'EMA / EU GMP' });
  const meta = s.sourceMetaFor('EU GDPR Art.32');
  assert.equal(s.normalizeJurisdictionNation(meta.nation), 'European Union');
  const ranked = s.rankChunks('GDPR privacy');
  assert.ok(ranked.length > 0);
});

check('QC pipeline preserves legacy fields and adds rubric/schema', () => {
  const s = boot({ fw: 'FDA', system: 'LIMS', domain: 'Pharma Mfg' }, ['B','C']);
  const ranked = s.rankChunks('Part 11 audit trail').slice(0, 12);
  const top = s.attachRankMeta(ranked, { jurisdictionSuppressed: [], scope: s.resolveScopeControls() });
  const raw = top.flatMap((c, i) => (c.reqs || [c.title]).slice(0, 2).map((rq, ri) => ({
    id: `LIMS-${String(i*2+ri+1).padStart(3,'0')}`,
    title: `Batch release: ${rq.slice(0,40)}`,
    type: 'business-control',
    regulation: c.reg,
    section: c.sec,
    regulatoryCriticality: i < 3 ? 'P0' : 'P1',
    regRef: `REQ-${i+1} · ${c.reg} ${c.sec}`,
    story: `For batch release, the business must implement ${rq.toLowerCase()} for the stated regulated outcome.`,
    ac: [
      `Given ${c.reg} ${c.sec} is identified, when LIMS supports batch release, then it implements: ${rq}.`,
      'Given QA reviews, when evidence is inspected, then results link to REQ.'
    ],
    accept: { action: rq, expected: 'compliance', pass_fail: 'QA review', traceable: `REQ-${i+1}` },
    invest: { independent:'yes', negotiable:'yes', valuable:'yes', estimable:'yes', small:'yes', testable:'yes' },
    sourceAuthority: 'US FDA / eCFR',
    sourceUrl: 'https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11',
    sourceExcerptVerified: false,
    sourceApprovalStatus: 'SME_PENDING',
    applicableNation: 'United States',
    sourceType: 'Regulation',
    sourceRequirement: rq,
    labels: ['audit-trail'],
    phase: 'Electronic record evidence',
    gamp: 'Cat.4'
  })));
  raw.push({ ...raw[0], id: 'LIMS-DUP' });

  const qc = s.applyQualityControls(raw, top, 'Part 11 audit trail', { regObjs: [], riskReg: [] });
  assert.ok(qc.stories.length >= 1);
  assert.ok(qc.stories.length < raw.length, 'duplicate should be suppressed');
  const story = qc.stories[0];
  ['id','title','type','story','ac','accept','invest','regRef','regulation','section','regulatoryCriticality']
    .forEach(f => assert.ok(story[f] != null && story[f] !== '', 'missing legacy field ' + f));
  assert.ok(story.validationRubric?.totalScore >= 0);
  assert.equal(story.validationRubric?.grade, 'REVIEW');
  assert.ok(story.validationRubric?.checks?.length >= 5);
  assert.equal(qc.healthcarePackage.schemaId, 'maras.fda.clinical-regulatory-assurance.v1');
  assert.equal(qc.fdaClinicalPackage.resourceType, 'FdaClinicalRegulatoryAssurancePackage');
  assert.ok(Array.isArray(qc.healthcarePackage.controls));
  assert.ok(qc.healthcarePackage.controls[0].validationRubric);
  assert.ok(qc.qcReport.compatibility.preservesLegacyStoryFields);
});

check('max output controls preserve the configured three-items-per-source ceiling', () => {
  const s = boot({});
  assert.ok(s.QC_CONFIG.maxScopedChunks > 0);
  assert.ok(s.QC_CONFIG.maxOutputItems >= s.QC_CONFIG.maxScopedChunks * 3);
  assert.equal(typeof s.QC_CONFIG.hardFilterLowRelevance, 'boolean');
});

check('every supported system returns a safe, relevant source set', () => {
  const matrix = {
    'LIMS':'audit trail data integrity validation laboratory',
    'MES':'batch audit trail change management validation',
    'SCADA / DCS':'access control security validation infrastructure',
    'Serialization':'traceability audit trail data integrity',
    'QMS':'CAPA change management deviation quality',
    'EDMS':'electronic records signature access control audit trail',
    'CDS':'ALCOA data integrity audit trail laboratory validation',
    'PV System':'privacy safety reporting CAPA',
    'EDC / eCRF':'clinical audit trail privacy electronic signature',
    'CTMS':'clinical privacy audit trail change management',
    'eTMF':'electronic records access control audit trail',
    'Safety Reporting':'safety reporting privacy CAPA',
    'Regulatory Info Mgmt':'regulatory submission change management validation',
    'ERP / SAP':'vendor access control audit trail outsourced',
    'Supply Chain':'vendor outsourced traceability quality agreement'
  };
  const selectBlock = extract(/(<select id="f-system"[\s\S]*?<\/select>)/, 'system selector');
  for (const [system, query] of Object.entries(matrix)) {
    assert.ok(selectBlock.includes(`value="${system}"`), `missing system option ${system}`);
    const domain = /EDC|CTMS|eTMF|PV System|Safety Reporting/.test(system) ? 'Clinical' : 'Pharma Mfg';
    const s = boot({ fw:'FDA', system, region:'United States', domain });
    const ranked = s.rankChunks(query);
    assert.ok(ranked.length > 0, `${system} returned no sources`);
    assert.ok(ranked.every(c => !c.licenseGate), `${system} included a licensed source`);
    assert.ok(ranked.every(c => !c.medicalDeviceOnly), `${system} included a medical-device-only source`);
    assert.ok(ranked[0]._qc.relevanceScore >= 1, `${system} top source was not relevant`);
  }
  assert.deepEqual(Object.keys(matrix).sort(), Object.keys(vm.runInContext('SYSTEM_AFFINITY', boot({}))).sort());
});

check('ingestion production gate holds incomplete sources and drives complete ones', () => {
  const s = boot({ fw: 'FDA', system: 'LIMS', domain: 'Pharma Mfg' });
  const held = s.evaluateSourceProductionGate({
    officialUrl: '', authority: '', documentClass: '', effectiveDate: '', capturedAt: '',
    fileHash: '', licenseTag: '', sourceApprovalStatus: 'SME_PENDING', parseStatus: 'PARSED', excerpt: 'x'
  });
  assert.equal(held.decision, 'HOLD');
  assert.ok(held.missing.includes('officialUrl'));
  const hash = 'a'.repeat(64);
  const drive = s.evaluateSourceProductionGate({
    officialUrl: 'https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11',
    authority: 'US FDA / eCFR',
    documentClass: 'Regulation',
    effectiveDate: '1997-08-20',
    capturedAt: '2026-08-21',
    fileHash: hash,
    licenseTag: 'PUBLIC_US_GOVERNMENT',
    sourceApprovalStatus: 'SME_APPROVED',
    parseStatus: 'PARSED',
    excerpt: 'Use of secure, computer-generated, time-stamped audit trails.'
  });
  assert.equal(drive.decision, 'DRIVE');
  const licensed = s.evaluateSourceProductionGate({
    officialUrl: 'https://ispe.org/publications/guidance-documents/gamp-5',
    authority: 'ISPE', documentClass: 'Licensed industry standard', effectiveDate: '2022-01-01',
    capturedAt: '2026-08-21', fileHash: hash, licenseTag: 'LICENSE_REQUIRED',
    sourceApprovalStatus: 'SME_APPROVED', parseStatus: 'PARSED', excerpt: 'IQ/OQ/PQ'
  });
  assert.equal(licensed.decision, 'HOLD');
  assert.equal(licensed.licenseBlocked, true);
  const before = s.rankChunks('audit trail LIMS Part 11').map(c => c.id);
  s.sbDocs.push({
    gate: { decision: 'HOLD' },
    chunk: { id: 'ing-held', cat: 'B', ingested: true, licenseGate: false, reg: 'Held', sec: 'x', title: 'Held', reqs: ['held'], kws: ['audit trail'] }
  });
  assert.deepEqual(s.rankChunks('audit trail LIMS Part 11').map(c => c.id), before);
  s.sbDocs[0] = {
    gate: { decision: 'DRIVE' },
    chunk: { id: 'ing-drive', cat: 'B', ingested: true, licenseGate: false, sourceKey: 'INGEST_test', reg: 'Customer SOP', sec: 'SOP-1', title: 'Batch release SOP', reqs: ['retain audit trail records'], excerpts: ['retain audit trail records'], kws: ['audit trail'] }
  };
  const after = s.rankChunks('audit trail LIMS Part 11');
  assert.ok(after.some(c => c.id === 'ing-drive'));
  const reqHold = s.evaluateRequirementIngestionGate({ name: 'spec.pdf', size: 12, parseStatus: 'UNSUPPORTED_BINARY', fileHash: hash, text: '' });
  assert.equal(reqHold.decision, 'HOLD');
  const reqDrive = s.evaluateRequirementIngestionGate({ name: 'spec.txt', size: 12, parseStatus: 'PARSED', fileHash: hash, text: 'Prove Part 11 audit trail' });
  assert.equal(reqDrive.decision, 'DRIVE');
  const parsed = s.parseRequirementPayload('json', '{"requirement":"Prove Part 11 audit trail for LIMS batch release"}');
  assert.equal(parsed.parseStatus, 'PARSED');
  assert.match(parsed.text, /Prove Part 11/);
});

check('global compare matrix cites US and EU audit trail with deltas', () => {
  const s = boot({ fw: 'FDA', system: 'LIMS', domain: 'Pharma Mfg' });
  s.compareMarketSel = new Set(['US', 'EU']);
  const rows = s.buildCompareRows();
  const audit = rows.find(r => r.topic.id === 'audit-trail');
  assert.ok(audit);
  assert.equal(audit.cells.US.status, 'ok');
  assert.equal(audit.cells.EU.status, 'ok');
  assert.ok(audit.cells.US.citation.includes('21 CFR'));
  assert.ok(audit.cells.EU.citation.includes('Annex 11'));
  const payload = s.buildCompareExportPayload();
  assert.equal(payload.schema, 'maras.global-regulation-compare.v1');
  assert.equal(payload.packageStatus, 'DRAFT_NOT_CONTROLLED');
});

check('SOP mapper surfaces gaps and inspection pack schema', () => {
  const s = boot({ fw: 'FDA', system: 'LIMS', domain: 'Pharma Mfg' });
  s.document.getElementById = (id) => ({
    value: id === 'f-client-delta' ? '' : id === 'req-ta' ? 'Part 11 audit trail LIMS' : id === 'f-gap-input' ? 'missing dual sign-off' : ''
  });
  const sop = s.mapSopToRegulations();
  assert.ok(sop.gaps.length >= 1, 'expected SOP gaps without client delta text');
  const insp = s.buildInspectionReadinessPack();
  assert.equal(insp.schema, 'maras.inspection-readiness.v1');
  assert.ok(insp.checklist.length >= 6);
  assert.ok(insp.mockQuestions.length >= 1);
});

if (failures.length) throw new Error(failures.join('\n'));

export const result = { status: 'PASS', checks: 10, systemsValidated: 15 };

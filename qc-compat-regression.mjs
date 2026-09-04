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
    H: { stories: [], review: {}, evidence: {}, qcReport: null, ragReplay: null },
    ragGraphEnabled: false,
    selItems: new Set(items),
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
  sandbox.RAG_GRAPH_CONFIG = vm.runInContext('RAG_GRAPH_CONFIG', sandbox);
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

check('FDA+EMA multi-select unions US and EU allowed nations', () => {
  const s = boot({ fw: 'FDA, EMA / EU GMP', system: 'LIMS', region: 'United States, European Union', domain: 'Pharma Mfg' });
  const scope = s.resolveScopeControls();
  assert.ok(scope.allowedNations, 'expected unioned allowedNations');
  assert.ok(scope.allowedNations.has('United States'));
  assert.ok(scope.allowedNations.has('European Union'));
  const ranked = s.rankChunks('21 CFR Part 11 audit trail');
  assert.ok(ranked.some(c => (c.reg||'').includes('21 CFR')));
  assert.ok(ranked.some(c => (c.reg||'').includes('EU GMP')), 'EU sources should remain when EMA/EU is also selected');
});

check('zero, one, many, and cleared framework/jurisdiction filters', () => {
  const none = boot({});
  assert.equal(none.resolveScopeControls().allowedNations, null, 'no selection applies no nation filter');
  const oneFw = boot({ fw: 'FDA' });
  const oneFwNations = oneFw.resolveScopeControls().allowedNations;
  assert.ok(oneFwNations.has('United States'));
  assert.ok(!oneFwNations.has('European Union'));
  const oneJur = boot({ fw: 'FDA', region: 'United States' });
  assert.deepEqual([...oneJur.resolveScopeControls().allowedNations].sort(), ['United States']);
  const many = boot({ fw: 'FDA, EMA / EU GMP', region: 'United States, European Union' });
  const manyN = many.resolveScopeControls().allowedNations;
  assert.ok(manyN.has('United States') && manyN.has('European Union'));
  const cleared = boot({ fw: '', region: '' });
  assert.equal(cleared.resolveScopeControls().allowedNations, null);
  const both = boot({ fw: 'FDA', region: 'European Union' });
  assert.ok(both.resolveScopeControls().allowedNations.has('European Union'));
  assert.ok(!both.resolveScopeControls().allowedNations.has('United States'), 'explicit jurisdiction is OR of selected markets only');
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
  s.compareMarketSel = new Set(['US', 'EU', 'HIPAA', 'GDPR']);
  s.selDomain = 'Pharma Mfg';
  s.document.getElementById = (id) => ({
    value: id === 'f-system' ? 'LIMS' : id === 'f-fw' ? 'FDA' : ''
  });
  const rows = s.buildCompareRows();
  const audit = rows.find(r => r.topic.id === 'audit-trail');
  assert.ok(audit);
  assert.equal(audit.cells.US.status, 'ok');
  assert.equal(audit.cells.EU.status, 'ok');
  assert.equal(audit.cells.HIPAA.status, 'ok');
  assert.equal(audit.cells.GDPR.status, 'ok');
  assert.ok(audit.cells.HIPAA.citation.includes('HIPAA'));
  assert.ok(audit.cells.GDPR.citation.includes('GDPR'));
  assert.equal(rows.find(r => r.topic.id === 'e-signature').cells.EU.status, 'ok');
  const ukRow = rows.find(r => r.topic.id === 'audit-trail');
  s.compareMarketSel = new Set(['US', 'EU', 'UK', 'INT']);
  const ukRows = s.buildCompareRows();
  const auditUk = ukRows.find(r => r.topic.id === 'audit-trail');
  assert.equal(auditUk.cells.UK.status, 'ok');
  assert.ok((auditUk.cells.UK.citation||'').includes('MHRA'));
  assert.ok(ukRows.some(r => r.topic.id === 'computerised-systems'));
  const payload = s.buildCompareExportPayload();
  assert.equal(payload.schema, 'maras.global-regulation-compare.v1');
  assert.equal(payload.packageStatus, 'DRAFT_NOT_CONTROLLED');
  assert.ok(payload.markets.some(m => /HIPAA/.test(m)));
  assert.ok(payload.markets.some(m => /GDPR/.test(m)));
});

check('SOP mapper surfaces gaps and inspection pack schema', () => {
  const s = boot({ fw: 'FDA', system: 'LIMS', domain: 'Pharma Mfg' });
  s.document.getElementById = (id) => ({
    value: id === 'f-client-delta' ? '' : id === 'req-ta' ? 'Part 11 audit trail LIMS' : id === 'f-gap-input' ? 'missing dual sign-off' : ''
  });
  const sop = s.mapSopToRegulations();
  assert.ok(sop.gaps.length >= 1, 'expected true gaps without library anchors');
  const sopLib = boot({ fw: 'FDA', system: 'LIMS', domain: 'Pharma Mfg' }, [], ['p11', 'sop', 'fda_di', 'ichq10', 'ichq9', 'capa']);
  sopLib.selItems = new Set(['p11', 'sop', 'fda_di', 'ichq10', 'ichq9', 'capa']);
  sopLib.document.getElementById = (id) => ({
    value: id === 'f-gap-input' ? 'audit trail dual sign-off' : id === 'req-ta' ? 'Part 11 audit trail' : ''
  });
  const mapped = sopLib.mapSopToRegulations();
  assert.ok(mapped.mappedCount >= 5, 'library anchors should map Part 11 and ICH controls');
  assert.equal(mapped.gaps.filter(g => /21 CFR Part 11/.test(g.regulation)).length, 0);
  const insp = sopLib.buildInspectionReadinessPack(mapped);
  assert.equal(insp.schema, 'maras.inspection-readiness.v1');
  assert.ok(insp.checklist.length >= 6);
  assert.ok(insp.evidenceRequests.length >= 1);
});

check('library remains complete and every outcome example is selectable', () => {
  const s = boot({});
  const n = s.TREE_DATA.reduce((a, g) => a + g.items.length, 0);
  assert.equal(n, 64);
  const reqSrc = html.match(/const REQ_EXAMPLES=(\[[\s\S]*?\]);\s*\nconst CATS=/);
  assert.ok(reqSrc, 'REQ_EXAMPLES not found');
  const examples = vm.runInNewContext(reqSrc[1]);
  assert.ok(examples.length >= 14);
  examples.forEach((ex, i) => {
    assert.ok(ex.text && ex.short, 'orphan example at ' + i);
  });
  assert.ok(html.includes('id="req-example-select"'));
  assert.ok(html.includes('function applyReqExample'));
  assert.ok(html.includes('id="sb-resizer"'));
  assert.ok(html.includes('sb-lib-gap'));
  assert.ok(html.includes('.sb-lib-gap{width:20px'));
  assert.ok(html.includes('.sb-tree{flex:none;overflow:visible'));
  assert.ok(!html.includes('sb-split-gap'));
});

const RAG_FIXTURES = [
  {
    name: 'generic IT requirement',
    req: 'Develop and configure API endpoints for ERP integration with role-based access and deployment controls',
    values: { fw: 'FDA', system: 'ERP / SAP', region: 'United States', domain: 'Pharma Mfg', outcome: 'Secure ERP integration' },
    expectIt: true,
    minPrimary: 0
  },
  {
    name: 'GxP laboratory system',
    req: 'LIMS batch-release audit trail and e-signature assurance under 21 CFR Part 11 with ALCOA+ data integrity',
    values: { fw: 'FDA', system: 'LIMS', region: 'United States', domain: 'Pharma Mfg', outcome: 'Defensible batch release' },
    expectIt: false,
    minPrimary: 1
  },
  {
    name: 'FDA clinical study-data submission',
    req: 'FDA clinical study data submission with essential records, audit trail, and ICH E6 GCP computerised systems controls',
    values: { fw: 'FDA', system: 'EDC / eCRF', region: 'United States', domain: 'Clinical', outcome: 'Inspection-ready clinical records' },
    expectIt: false,
    minPrimary: 1
  },
  {
    name: 'QA CAPA',
    req: 'CAPA and deviation management controls with root-cause traceability and effectiveness verification',
    values: { fw: 'FDA', system: 'QMS', region: 'United States', domain: 'Pharma Mfg', outcome: 'Closed quality events' },
    expectIt: false,
    minPrimary: 0
  }
];

function scoreRagFixtureRubric(s, story) {
  const qg = s.buildQualityGateSummary(story);
  const rub = s.scoreValidationRubric(story, s.resolveScopeControls());
  return {
    storyFormat: qg.storyFormat ? 1 : 0,
    clarity: qg.clarity ? 1 : 0,
    testability: qg.testability ? 1 : 0,
    grammar: qg.grammar ? 1 : 0,
    invest: qg.invest >= 5 ? 1 : 0,
    rubricTotal: rub.totalScore
  };
}

check('RAG graph fixtures: parse retrieve rerank synthesize verify', () => {
  for (const fx of RAG_FIXTURES) {
    const s = boot(fx.values, ['B', 'C', 'F'], ['p11', 'alcoa', 'gamp5', 'capa', 'iche6']);
    s.selItems = new Set(['p11', 'alcoa', 'gamp5', 'capa', 'iche6']);
    s.ragGraphEnabled = true;
    s.H = { ragReplay: { userOverrides: { forceInclude: [], exclude: [] } } };
    const ctx = { sys: fx.values.system, outcome: fx.values.outcome, auditGap: 'test gap' };
    const graph = s.runRagGraph(fx.req, ctx);
    assert.equal(graph.ok, true, fx.name + ' graph failed');
    const p = graph.stages.parse.output;
    assert.ok(p.requirement_id, fx.name + ' missing requirement_id');
    assert.ok(p.raw_text.length > 10, fx.name + ' parse raw_text');
    assert.ok(p.scope_hints.jurisdiction, fx.name + ' scope_hints');
    const candidates = graph.stages.retrieve.output.candidates;
    assert.ok(candidates.length > 0, fx.name + ' retrieve empty');
    candidates.forEach(c => {
      assert.ok(c.cite.source_id, fx.name + ' missing cite source_id');
      assert.ok(c.cite.regulation, fx.name + ' missing regulation');
    });
    const rerank = graph.stages.rerank.output;
    assert.ok(rerank.items.every(i => ['primary','supporting','contextual','suppressed','not_applicable'].includes(i.label)), fx.name + ' bad label');
    if (fx.minPrimary) assert.ok(rerank.primaryCount >= fx.minPrimary, fx.name + ' primary count');
  }
});

check('RAG graph fixtures: rubric dimensions on synthesized mock story', () => {
  for (const fx of RAG_FIXTURES) {
    const s = boot(fx.values, ['B', 'C', 'F'], ['p11', 'alcoa', 'capa']);
    s.selItems = new Set(['p11', 'alcoa', 'capa']);
    s.ragGraphEnabled = true;
    s.H = { ragReplay: { userOverrides: { forceInclude: [], exclude: [] } } };
    const graph = s.runRagGraph(fx.req, { sys: fx.values.system, outcome: fx.values.outcome, auditGap: '' });
    s.H.ragReplay = graph;
    const synth = graph.stages.synthesize.output;
    if (fx.expectIt) assert.equal(synth.it_pbi_included, true, fx.name + ' IT PBI flag');
    else assert.equal(synth.it_pbi_included, false, fx.name + ' unexpected IT PBI');
    const obl = synth.obligations[0];
    const mockStory = {
      id: 'TST-001', title: 'Test: ' + (obl?.text || 'control').slice(0, 40),
      story: 'For regulated operations, the business must implement controls so that outcomes remain traceable and measurable.',
      regulation: obl?.cite?.regulation || '21 CFR Part 11', section: obl?.cite?.section || '§11.10',
      regRef: 'REQ-TST · ' + (obl?.cite?.regulation || '21 CFR Part 11'),
      ac: [
        'Given a regulated source, when the system operates, then controls are demonstrable.',
        'Given QA reviews, when evidence is inspected, then pass/fail links to REQ-TST.'
      ],
      accept: { action: 'control', expected: 'evidence', pass_fail: 'QA', traceable: 'REQ-TST' },
      invest: { independent:'yes', negotiable:'yes', valuable:'yes', estimable:'yes', small:'yes', testable:'yes' },
      sourceAuthority: 'US FDA', sourceUrl: 'https://www.ecfr.gov', sourceExcerptVerified: false, sourceApprovalStatus: 'SME_PENDING'
    };
    s.ragCompleteVerify(fx.req, [mockStory]);
    const scores = scoreRagFixtureRubric(s, mockStory);
    assert.ok(scores.storyFormat === 1, fx.name + ' storyFormat');
    assert.ok(scores.clarity === 1, fx.name + ' clarity/grammar');
    assert.ok(scores.testability === 1, fx.name + ' testability');
    assert.ok(scores.invest === 1, fx.name + ' invest');
    assert.ok(scores.rubricTotal >= 0, fx.name + ' rubric');
  }
});

check('RAG graph disabled preserves legacy rankChunks path', () => {
  const s = boot({ fw: 'FDA', system: 'LIMS', domain: 'Pharma Mfg' });
  s.ragGraphEnabled = false;
  s.H = { ragReplay: null };
  const legacy = s.rankChunks('audit trail LIMS Part 11');
  const viaHelper = s.ragGetActiveRanked('audit trail LIMS Part 11');
  assert.deepEqual(viaHelper.map(c => c.id), legacy.map(c => c.id));
});

function bootRag(values, cats = ['B', 'C', 'F'], items = ['p11', 'alcoa', 'gamp5', 'capa']) {
  const s = boot(values, cats, items);
  s.selItems = new Set(items);
  s.ragGraphEnabled = true;
  s.H = { ragReplay: { userOverrides: { forceInclude: [], exclude: [] } } };
  return s;
}

check('hybrid routing: explicit section refs yield deterministic hits', () => {
  const s = bootRag({ fw: 'FDA', system: 'LIMS', region: 'United States', domain: 'Pharma Mfg' });
  const req = 'The LIMS must satisfy 21 CFR Part 11 §11.10 audit trail and access controls for batch release in GMP manufacturing.';
  const parsed = s.ragParse(req, { sys: 'LIMS' });
  assert.ok((parsed.explicit_refs || []).length >= 1, 'expected explicit_refs from §11.10 / Part 11');
  const out = s.ragRetrieve(req, parsed);
  assert.equal(out.hybrid, true);
  const det = (out.route_log || []).find(r => r.stage === 'deterministic');
  assert.ok(det && det.count >= 1, 'deterministic stage should return hits');
  const detHits = out.candidates.filter(c => (c.provenance || []).includes('deterministic'));
  assert.ok(detHits.length >= 1, 'at least one candidate from deterministic route');
  assert.ok(detHits.some(c => /21 CFR Part 11/i.test(c.chunk?.reg || '')), 'Part 11 chunk in deterministic hits');
});

check('hybrid routing: graph expansion adds related sources without bloat', () => {
  const s = bootRag({ fw: 'FDA', system: 'LIMS', region: 'United States', domain: 'Pharma Mfg' });
  const req = '21 CFR Part 11 §11.10 audit trail LIMS batch release e-signature ALCOA data integrity';
  const parsed = s.ragParse(req, { sys: 'LIMS' });
  const out = s.ragRetrieve(req, parsed);
  const graph = (out.route_log || []).find(r => r.stage === 'graph');
  assert.ok(graph, 'graph stage should run for explicit refs with seeds');
  if (graph.count > 0) {
    const graphHits = out.candidates.filter(c => (c.provenance || []).includes('graph'));
    assert.ok(graphHits.length >= 1, 'graph provenance on expanded candidates');
    assert.ok(out.candidates.length <= s.RAG_GRAPH_CONFIG.hybridMaxCandidates + 2, 'merge should respect candidate cap');
  }
});

check('hybrid routing: vector stage runs for vague requirements', () => {
  const s = bootRag({ fw: 'FDA', system: 'QMS', region: 'United States', domain: 'Pharma Mfg' });
  const req = 'Improve overall quality and operational compliance across manufacturing without naming a specific regulation, section, or control identifier in this statement.';
  const parsed = s.ragParse(req, { sys: 'QMS' });
  const out = s.ragRetrieve(req, parsed);
  const vector = (out.route_log || []).find(r => r.stage === 'vector');
  assert.ok(vector, 'vector stage should be present');
  assert.ok(['tfidf-cosine-pseudo', 'skipped-explicit-refs'].includes(vector.method), 'vector method labeled');
  assert.ok(out.candidates.length > 0, 'vague query still returns merged candidates');
});

check('hybrid routing: provenance attached to every candidate', () => {
  const s = bootRag({ fw: 'FDA', system: 'LIMS', region: 'United States', domain: 'Pharma Mfg' });
  const req = 'LIMS batch-release audit trail and e-signature assurance under 21 CFR Part 11 with ALCOA+ data integrity';
  const graph = s.runRagGraph(req, { sys: 'LIMS', outcome: 'Defensible batch release', auditGap: '' });
  assert.equal(graph.ok, true);
  const candidates = graph.stages.retrieve.output.candidates;
  assert.ok(candidates.length > 0);
  candidates.forEach((c, i) => {
    assert.ok(Array.isArray(c.provenance) && c.provenance.length > 0, 'missing provenance at index ' + i);
    assert.ok(c.provenance.every(m => ['deterministic', 'graph', 'vector', 'legacy', 'legacy-fallback'].includes(m)), 'invalid provenance tag');
  });
  const rerank = graph.stages.rerank.output;
  rerank.items.forEach((item, i) => {
    assert.ok(Array.isArray(item.provenance) && item.provenance.length > 0, 'rerank missing provenance at ' + i);
  });
});

if (failures.length) throw new Error(failures.join('\n'));

export const result = { status: 'PASS', checks: 19, systemsValidated: 15, ragFixtures: RAG_FIXTURES.length };

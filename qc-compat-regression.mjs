/**
 * Non-browser regression checks for MARAS QC compatibility.
 * Ensures QC controls do not empty the corpus or drop legacy story fields.
 */
import fs from 'fs';
import vm from 'vm';
import assert from 'assert';

const html = fs.readFileSync(new URL('./index.html', import.meta.url), 'utf8');

function extract(re, label) {
  const m = html.match(re);
  if (!m) throw new Error(`Could not extract ${label}`);
  return m[1];
}

const gxpChunksSrc = extract(/const GXP_CHUNKS=(\[[\s\S]*?\]);\s*\nconst /, 'GXP_CHUNKS');
const treeDataSrc = extract(/const TREE_DATA=(\[[\s\S]*?\]);\s*\n/, 'TREE_DATA');

// Pull QC layer through rankChunks (ends before AUTO PREFIX)
const qcStart = html.indexOf('const QC_CONFIG = {');
const qcEnd = html.indexOf('/* ─── AUTO PREFIX');
if (qcStart < 0 || qcEnd < 0) throw new Error('QC block bounds not found');
const qcSrc = html.slice(qcStart, qcEnd);

// sourceMetaFor near end
const sm = html.match(/function sourceMetaFor\(reg\)\{[\s\S]*?\n\}/);
if (!sm) throw new Error('sourceMetaFor not found');

function makeDom(values = {}) {
  const store = {
    'f-fw': values.fw ?? '',
    'f-system': values.system ?? '',
    'f-client-region': values.region ?? '',
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
    Set, Map, Array, Object, String, Math, Date, JSON, Number, Boolean,
    document: makeDom(values),
    selCatsSet: new Set(cats),
    selItems: new Set(items),
    demoMode: true,
    TREE_DATA: [],
    GXP_CHUNKS: [],
  };
  vm.createContext(sandbox);
  vm.runInContext(`TREE_DATA = ${treeDataSrc};`, sandbox);
  vm.runInContext(`GXP_CHUNKS = ${gxpChunksSrc};`, sandbox);
  vm.runInContext(qcSrc, sandbox);
  vm.runInContext(sm[0], sandbox);
  // autoPrefix stub used by normalize
  vm.runInContext(`function autoPrefix(){ return 'GXP'; }`, sandbox);
  // vm `const` bindings are not auto-copied onto the context object
  sandbox.QC_CONFIG = vm.runInContext('QC_CONFIG', sandbox);
  sandbox.FDA_CLINICAL_DATA_SCHEMA = vm.runInContext('FDA_CLINICAL_DATA_SCHEMA', sandbox);
  return sandbox;
}

function mainStyleRank(chunks, req, activeCats, treeCats) {
  const qt = (req || '').toLowerCase();
  return chunks.filter(c => {
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
  try { fn(); console.log('PASS', name); }
  catch (e) { failures.push(name + ': ' + e.message); console.error('FAIL', name, e.message); }
}

// 1) Empty framework — same category coverage as main (no jurisdiction wipe)
check('empty-fw preserves full corpus like main', () => {
  const s = boot({});
  const ranked = s.rankChunks('audit trail LIMS Part 11');
  const main = mainStyleRank(s.GXP_CHUNKS, 'audit trail LIMS Part 11', null, null);
  assert.strictEqual(ranked.length, main.length, `expected ${main.length} got ${ranked.length}`);
  assert.ok(ranked._scope, 'rank meta attached');
  assert.ok(ranked.length > 12, 'full list returned (not hard-sliced)');
});

// 2) Category scope identical to main
check('category scope matches main filter', () => {
  const cats = ['B','C','F'];
  const s = boot({ fw: 'FDA', system: 'LIMS' }, cats);
  const ranked = s.rankChunks('audit trail e-signature validation');
  const main = mainStyleRank(s.GXP_CHUNKS, 'audit trail e-signature validation', new Set(cats), null);
  // QC may jurisdiction-filter EU under FDA, so subset of main — never empty, never outside cats
  assert.ok(ranked.length > 0);
  ranked.forEach(c => assert.ok(cats.includes(c.cat), 'out of scope cat ' + c.cat));
  assert.ok(ranked.length <= main.length);
  // Every kept chunk was in main's category-filtered set
  const mainIds = new Set(main.map(c => c.id));
  ranked.forEach(c => assert.ok(mainIds.has(c.id)));
});

// 3) FDA jurisdiction: EU Annex suppressed when US alternatives exist; never empty
check('FDA jurisdiction filters EU when US alternatives exist', () => {
  const s = boot({ fw: 'FDA', system: 'LIMS', region: 'United States' });
  const ranked = s.rankChunks('21 CFR Part 11 audit trail');
  assert.ok(ranked.length > 0);
  const eu = ranked.filter(c => (c.reg||'').includes('EU GMP'));
  assert.strictEqual(eu.length, 0, 'EU sources should be hard-filtered under FDA when US alts exist');
  assert.ok((ranked._jurisdictionSuppressed || []).length >= 1);
  assert.ok(ranked.some(c => (c.reg||'').includes('21 CFR')));
});

// 4) Nation normalization maps GDPR EU/EEA → European Union
check('nation normalization for GDPR under EMA', () => {
  const s = boot({ fw: 'EMA / EU GMP' });
  const meta = s.sourceMetaFor('EU GDPR Art.32');
  assert.strictEqual(s.normalizeJurisdictionNation(meta.nation), 'European Union');
  const ranked = s.rankChunks('GDPR privacy');
  assert.ok(ranked.length > 0);
});

// 5) Duplicate suppression + normalization + rubric + FDA schema
check('QC pipeline produces rubric + FDA clinical schema without dropping legacy fields', () => {
  const s = boot({ fw: 'FDA', system: 'LIMS' }, ['B','C']);
  const ranked = s.rankChunks('Part 11 audit trail').slice(0, 12);
  // re-attach meta after slice (demo engine does this)
  const top = s.attachRankMeta(ranked, {
    jurisdictionSuppressed: ranked._jurisdictionSuppressed || [],
    scope: ranked._scope
  });
  const raw = top.flatMap((c, i) => (c.reqs || [c.title]).slice(0, 2).map((rq, ri) => ({
    id: `LIMS-${String(i*2+ri+1).padStart(3,'0')}`,
    title: `Batch release: ${rq.slice(0,40)}`,
    type: 'business-control',
    regulation: c.reg,
    section: c.sec,
    regulatoryCriticality: i < 3 ? 'P0' : 'P1',
    regRef: `REQ-${i+1} · ${c.reg} ${c.sec}`,
    story: `For batch release the business must ${rq}`,
    ac: [
      `Given ${c.reg} ${c.sec} is approved, when LIMS supports batch release, then it implements: ${rq}.`,
      `Given QA reviews, when evidence is inspected, then results link to REQ.`
    ],
    accept: { action: rq, expected: 'compliance', pass_fail: 'QA review', traceable: `REQ-${i+1}` },
    invest: { independent:'yes', negotiable:'yes', valuable:'yes', estimable:'yes', small:'yes', testable:'yes' },
    sourceAuthority: 'US FDA / eCFR',
    applicableNation: 'United States',
    sourceType: 'Regulation',
    sourceRequirement: rq,
    labels: ['audit-trail'],
    phase: 'Electronic record evidence',
    gamp: 'Cat.4'
  })));
  // Inject an exact duplicate
  raw.push({ ...raw[0], id: 'LIMS-DUP' });

  const qc = s.applyQualityControls(raw, top, 'Part 11 audit trail', { regObjs: [], riskReg: [] });
  assert.ok(qc.stories.length >= 1);
  assert.ok(qc.stories.length < raw.length, 'duplicate should be suppressed');
  const story = qc.stories[0];
  ['id','title','type','story','ac','accept','invest','regRef','regulation','section','regulatoryCriticality']
    .forEach(f => assert.ok(story[f] != null && story[f] !== '', 'missing legacy field ' + f));
  assert.ok(story.validationRubric?.totalScore >= 0);
  assert.ok(story.validationRubric?.checks?.length >= 5);
  assert.strictEqual(qc.healthcarePackage.schemaId, 'maras.fda.clinical-regulatory-assurance.v1');
  assert.strictEqual(qc.fdaClinicalPackage.resourceType, 'FdaClinicalRegulatoryAssurancePackage');
  assert.ok(Array.isArray(qc.healthcarePackage.controls));
  assert.ok(qc.healthcarePackage.controls[0].validationRubric);
  assert.ok(qc.qcReport.compatibility.preservesLegacyStoryFields);
});

// 6) Max output items does not shrink below historical 12×3 demo ceiling for typical packages
check('maxOutputItems is at least 36 (compat with main demo ceiling)', () => {
  const s = boot({});
  assert.ok(s.QC_CONFIG.maxOutputItems >= 36);
  assert.strictEqual(s.QC_CONFIG.maxScopedChunks, 12);
  assert.strictEqual(s.QC_CONFIG.hardFilterLowRelevance, false);
});

if (failures.length) {
  console.error('\n' + failures.length + ' failure(s)');
  process.exit(1);
}
console.log('\nAll QC compatibility regressions passed.');

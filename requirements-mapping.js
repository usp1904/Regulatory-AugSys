/* MARAS Requirements Mapping Foundation: deterministic, draft-only traceability gate.
   Completeness checks are not legal interpretation, source verification, or proof of compliance. */
(function () {
  'use strict';
  if (window.MARASRequirementsMapper) return;
  var records = [];
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (v) { return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
  }); };
  var val = function (id) { return $(id) ? $(id).value.trim() : ''; };
  var makeId = function () { return 'MAP-' + Date.now().toString(36).toUpperCase() + '-' + Math.random().toString(36).slice(2,7).toUpperCase(); };

  function validate(r) {
    var checks = [
      ['Source identity and version', !!r.sourceId && !!r.sourceVersion],
      ['Stable clause/section reference', !!r.clauseId],
      ['Source excerpt captured', r.sourceExcerpt.length >= 12],
      ['Atomic obligation stated', r.obligation.length >= 12],
      ['Applicability decision recorded', r.applicability !== 'UNDECIDED'],
      ['System evidence or explicit unknown recorded', r.systemFinding === 'UNKNOWN' ? !!r.systemEvidence : (r.systemFinding !== 'NOT_ASSESSED' && !!r.systemEvidence)],
      ['Interpretation/decision recorded', r.decision.length >= 12],
      ['Decision is explicitly confirmed', r.decisionStatus === 'CONFIRMED'],
      ['Open clarification has an assigned owner', !r.question || !!r.questionOwner],
      ['Dependencies are resolved or not required', r.dependencyStatus !== 'OPEN'], 
      ['Decision owner identified', !!r.decisionOwner],
      ['Observable business requirement', r.requirement.length >= 20],
      ['Testable acceptance criteria', r.acceptanceCriteria.length >= 20],
      ['Verification method/evidence defined', r.testEvidence.length >= 12]
    ].map(function (c) { return {label:c[0], pass:c[1]}; });
    var blockers = checks.filter(function (c) { return !c.pass; }).map(function (c) { return c.label; });
    if (r.applicability === 'NOT_APPLICABLE' && !r.notApplicableRationale) blockers.push('Not-applicable rationale is required');
    if (r.systemFinding === 'NOT_APPLICABLE' && !r.notApplicableRationale) blockers.push('System not-applicable rationale is required');
    if (!r.approver) blockers.push('Named approver is required');
    if (r.approvalDecision !== 'APPROVED') blockers.push('Approver has not approved this mapping');
    return {
      checks:checks, blockers:blockers,
      decision:blockers.length ? 'BLOCKED_DRAFT' : 'READY_FOR_CONTROLLED_REVIEW',
      releaseReady:blockers.length === 0,
      note:'Automated completeness check only. It does not prove legal interpretation, source authenticity, or regulatory compliance.'
    };
  }

  function buildRecord() {
    var r = {
      schemaVersion:'maras.requirements-mapping.v1', mappingId:makeId(), createdAt:new Date().toISOString(),
      packageStatus:'DRAFT_NOT_CONTROLLED',
      source:{sourceId:val('maras-rm-source-id'),title:val('maras-rm-source-title'),authority:val('maras-rm-authority'),
        version:val('maras-rm-source-version'),effectiveDate:val('maras-rm-effective-date'),capturedAt:val('maras-rm-captured-at'),
        url:val('maras-rm-source-url'),clauseId:val('maras-rm-clause-id'),excerpt:val('maras-rm-source-excerpt')},
      obligation:val('maras-rm-obligation'), applicability:val('maras-rm-applicability'),
      notApplicableRationale:val('maras-rm-na-rationale'),
      system:{name:val('maras-rm-system-name'),finding:val('maras-rm-system-finding'),evidenceRef:val('maras-rm-system-evidence'),observedAt:val('maras-rm-evidence-date')},
      clarification:{question:val('maras-rm-question'),questionOwner:val('maras-rm-question-owner'), questionDueDate:val('maras-rm-question-due'),
        decisionStatus:val('maras-rm-decision-status'), decision:val('maras-rm-decision'),owner:val('maras-rm-decision-owner'),
        rationale:val('maras-rm-decision-rationale'),dependency:val('maras-rm-dependency'),dependencyStatus:val('maras-rm-dependency-status')},
      requirement:val('maras-rm-requirement'),
      pbi:{title:val('maras-rm-pbi-title'),acceptanceCriteria:val('maras-rm-ac'),testEvidence:val('maras-rm-test-evidence')},
      approval:{approver:val('maras-rm-approver'),decision:val('maras-rm-approval'),comment:val('maras-rm-approval-comment'),
        approvedAt:val('maras-rm-approval') === 'APPROVED' ? new Date().toISOString() : null}
    };
    r.validation = validate({
      sourceId:r.source.sourceId, sourceVersion:r.source.version, clauseId:r.source.clauseId,
      sourceExcerpt:r.source.excerpt, obligation:r.obligation, applicability:r.applicability,
      notApplicableRationale:r.notApplicableRationale, systemFinding:r.system.finding, systemEvidence:r.system.evidenceRef,
      decision:r.clarification.decision, decisionStatus:r.clarification.decisionStatus, question:r.clarification.question,
      questionOwner:r.clarification.questionOwner, dependencyStatus:r.clarification.dependencyStatus,
      decisionOwner:r.clarification.owner, requirement:r.requirement,
      acceptanceCriteria:r.pbi.acceptanceCriteria, testEvidence:r.pbi.testEvidence,
      approver:r.approval.approver, approvalDecision:r.approval.decision
    });
    return r;
  }

  var style = document.createElement('style');
  style.textContent = '#maras-rm-launch{position:fixed;right:18px;bottom:18px;z-index:9997;border:0;border-radius:999px;padding:11px 16px;background:#153b63;color:#fff;font:600 12px Inter,Arial,sans-serif;box-shadow:0 4px 18px #0003;cursor:pointer}' +
    '#maras-rm-overlay{position:fixed;inset:0;z-index:9998;background:#0b1728a8;display:none;align-items:stretch;justify-content:flex-end}' +
    '#maras-rm-panel{width:min(780px,100vw);height:100%;overflow:auto;background:#f7f8fa;color:#172033;font:13px/1.45 Inter,Arial,sans-serif;box-shadow:-8px 0 30px #0002}' +
    '#maras-rm-panel *{box-sizing:border-box}.maras-rm-head{position:sticky;top:0;z-index:2;background:#102c4b;color:#fff;padding:16px 20px;display:flex;align-items:center;gap:12px}' +
    '.maras-rm-head h2{font-size:16px;margin:0;flex:1}.maras-rm-close{border:1px solid #ffffff55;background:transparent;color:#fff;border-radius:6px;padding:6px 10px;cursor:pointer}' +
    '.maras-rm-body{padding:16px 20px 28px}.maras-rm-notice{padding:10px 12px;border:1px solid #e6c779;background:#fff9e7;border-radius:7px;margin-bottom:14px;color:#654b12}' +
    '.maras-rm-section{font-size:12px;font-weight:700;color:#153b63;margin:18px 0 8px;border-bottom:1px solid #dce2ea;padding-bottom:5px}' +
    '.maras-rm-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.maras-rm-field{display:flex;flex-direction:column;gap:4px;min-width:0}.maras-rm-field.wide{grid-column:1/-1}' +
    '.maras-rm-field label{font-size:11px;font-weight:600;color:#374151}.maras-rm-field input,.maras-rm-field select,.maras-rm-field textarea{width:100%;border:1px solid #cbd5e1;border-radius:5px;padding:8px;font:12px Inter,Arial,sans-serif;background:#fff;color:#111827}' +
    '.maras-rm-field textarea{min-height:64px;resize:vertical}.maras-rm-help{font-size:10px;color:#64748b}.maras-rm-actions{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}' +
    '.maras-rm-btn{border:1px solid #cbd5e1;background:#fff;border-radius:6px;padding:8px 12px;font:600 12px Inter,Arial,sans-serif;cursor:pointer;color:#1f2937}.maras-rm-btn.primary{background:#1767b1;border-color:#1767b1;color:#fff}' +
    '.maras-rm-status{padding:10px 12px;border-radius:6px;background:#fff;border:1px solid #dbe2ea;margin:12px 0}.maras-rm-status.blocked{border-color:#e7b3b3;background:#fff5f5}.maras-rm-status.ready{border-color:#9bd5b6;background:#f1fff6}' +
    '.maras-rm-list{display:grid;gap:8px}.maras-rm-item{background:#fff;border:1px solid #dbe2ea;border-radius:7px;padding:10px}.maras-rm-item h4{margin:0 0 4px;font-size:12px}.maras-rm-item p{font-size:11px;color:#4b5563;margin:3px 0;overflow-wrap:anywhere}' +
    '@media(max-width:560px){.maras-rm-grid{grid-template-columns:1fr}.maras-rm-field.wide{grid-column:auto}.maras-rm-body{padding:12px}}';
  document.head.appendChild(style);

  var overlay = document.createElement('div');
  overlay.id = 'maras-rm-overlay';
  overlay.innerHTML = '<section id="maras-rm-panel" role="dialog" aria-modal="true" aria-labelledby="maras-rm-title">' +
    '<header class="maras-rm-head"><h2 id="maras-rm-title">Requirements Mapping Workbench</h2><button class="maras-rm-close" type="button" id="maras-rm-close">Close</button></header>' +
    '<div class="maras-rm-body"><div class="maras-rm-notice"><b>Draft-only control:</b> This workbench checks completeness and traceability fields; it does not verify legal meaning, source authenticity, or compliance. Do not enter confidential or patient-identifiable data. Records remain in page memory until exported.</div>' +
    '<form id="maras-rm-form">' +
    '<div class="maras-rm-section">1 · Source evidence</div><div class="maras-rm-grid">' +
    '<div class="maras-rm-field"><label>Source ID *</label><input id="maras-rm-source-id" required placeholder="SRC-FDA-001"></div>' +
    '<div class="maras-rm-field"><label>Source title / authority *</label><input id="maras-rm-source-title" required placeholder="Official document title"></div>' +
    '<div class="maras-rm-field"><label>Issuing authority</label><input id="maras-rm-authority" placeholder="Regulator / standards body"></div>' +
    '<div class="maras-rm-field"><label>Version / revision / edition *</label><input id="maras-rm-source-version" required placeholder="Revision or publication date"></div>' +
    '<div class="maras-rm-field"><label>Effective date</label><input id="maras-rm-effective-date" type="date"></div>' +
    '<div class="maras-rm-field"><label>Capture date *</label><input id="maras-rm-captured-at" type="date" required></div>' +
    '<div class="maras-rm-field wide"><label>Official source URL</label><input id="maras-rm-source-url" type="url" placeholder="https://..."></div>' +
    '<div class="maras-rm-field"><label>Stable clause / section ID *</label><input id="maras-rm-clause-id" required placeholder="e.g. §11.10(a)"></div>' +
    '<div class="maras-rm-field wide"><label>Exact excerpt / evidence text *</label><textarea id="maras-rm-source-excerpt" required placeholder="Paste the relevant excerpt and preserve its source reference"></textarea><span class="maras-rm-help">Excerpt capture does not prove that the source is current or applicable.</span></div></div>' +
    '<div class="maras-rm-section">2 · Obligation and applicability</div><div class="maras-rm-grid">' +
    '<div class="maras-rm-field wide"><label>Atomic obligation (what must be true) *</label><textarea id="maras-rm-obligation" required placeholder="State one obligation separately from interpretation"></textarea></div>' +
    '<div class="maras-rm-field"><label>Applicability *</label><select id="maras-rm-applicability"><option value="UNDECIDED">Undecided</option><option value="APPLICABLE">Applicable</option><option value="NOT_APPLICABLE">Not applicable</option><option value="CONDITIONAL">Conditional / scope to confirm</option></select></div>' +
    '<div class="maras-rm-field"><label>Not-applicable rationale</label><input id="maras-rm-na-rationale" placeholder="Required if not applicable"></div></div>' +
    '<div class="maras-rm-section">3 · Existing system evidence</div><div class="maras-rm-grid">' +
    '<div class="maras-rm-field"><label>System / process *</label><input id="maras-rm-system-name" required placeholder="System Owner system"></div>' +
    '<div class="maras-rm-field"><label>Finding *</label><select id="maras-rm-system-finding"><option value="NOT_ASSESSED">Not assessed</option><option value="UNKNOWN">Unknown — evidence needed</option><option value="VERIFIED_MATCH">Verified match</option><option value="PARTIAL_MATCH">Partial match</option><option value="VERIFIED_GAP">Verified gap</option><option value="NOT_APPLICABLE">Not applicable — rationale required</option></select></div>' +
    '<div class="maras-rm-field wide"><label>Evidence reference or explicit unknown reason *</label><textarea id="maras-rm-system-evidence" required placeholder="Test/report/configuration/document reference, or describe missing evidence"></textarea></div>' +
    '<div class="maras-rm-field"><label>Evidence observed date</label><input id="maras-rm-evidence-date" type="date"></div></div>' +
    '<div class="maras-rm-section">4 · Clarification and decision</div><div class="maras-rm-grid">' +
    '<div class="maras-rm-field wide"><label>Question for System Owner / SME / Product Owner</label><textarea id="maras-rm-question" placeholder="What needs clarification?"></textarea></div>' +
    '<div class="maras-rm-field"><label>Question owner</label><input id="maras-rm-question-owner" placeholder="Person / accountable role"></div>' +
    '<div class="maras-rm-field"><label>Question due date</label><input id="maras-rm-question-due" type="date"></div>' +
    '<div class="maras-rm-field"><label>Decision status *</label><select id="maras-rm-decision-status"><option value="OPEN">Open — clarification needed</option><option value="PROPOSED">Proposed — awaiting confirmation</option><option value="CONFIRMED">Confirmed by accountable owner</option><option value="REJECTED">Rejected — rework required</option></select></div>' +
    '<div class="maras-rm-field wide"><label>Decision / interpretation *</label><textarea id="maras-rm-decision" required placeholder="Record the decision and its rationale, or current proposal"></textarea></div>' +
    '<div class="maras-rm-field"><label>Decision owner *</label><input id="maras-rm-decision-owner" required placeholder="Accountable owner / role"></div>' +
    '<div class="maras-rm-field"><label>Dependency / blocker</label><input id="maras-rm-dependency" placeholder="What must be resolved first?"></div>' +
    '<div class="maras-rm-field"><label>Dependency status *</label><select id="maras-rm-dependency-status"><option value="NOT_REQUIRED">No dependency</option><option value="OPEN">Open — blocks release</option><option value="RESOLVED">Resolved</option></select></div>' +
    '<div class="maras-rm-field wide"><label>Decision rationale</label><textarea id="maras-rm-decision-rationale" placeholder="Why this interpretation applies to this system and scope"></textarea></div></div>' +
    '<div class="maras-rm-section">5 · Requirement, PBI and verification</div><div class="maras-rm-grid">' +
    '<div class="maras-rm-field wide"><label>Business requirement (observable outcome) *</label><textarea id="maras-rm-requirement" required placeholder="The system/process shall ..."></textarea></div>' +
    '<div class="maras-rm-field wide"><label>Draft PBI title *</label><input id="maras-rm-pbi-title" required placeholder="Verb + business outcome"></div>' +
    '<div class="maras-rm-field wide"><label>Acceptance criteria (positive, negative, boundary/failure as relevant) *</label><textarea id="maras-rm-ac" required placeholder="Given ... When ... Then ...; include failure paths where relevant"></textarea></div>' +
    '<div class="maras-rm-field wide"><label>Verification method / evidence artifact *</label><textarea id="maras-rm-test-evidence" required placeholder="Test case, expected result, evidence artifact and owner"></textarea></div></div>' +
    '<div class="maras-rm-section">6 · Human approval gate</div><div class="maras-rm-grid">' +
    '<div class="maras-rm-field"><label>Approver name / accountable role *</label><input id="maras-rm-approver" required placeholder="SME / QA / System Owner"></div>' +
    '<div class="maras-rm-field"><label>Approval decision *</label><select id="maras-rm-approval"><option value="PENDING">Pending review</option><option value="APPROVED">Approved for controlled review</option><option value="CHANGES_REQUIRED">Changes required</option><option value="REJECTED">Rejected</option></select></div>' +
    '<div class="maras-rm-field wide"><label>Approval comments / conditions</label><textarea id="maras-rm-approval-comment" placeholder="Conditions, review notes or rationale"></textarea></div></div>' +
    '<div class="maras-rm-actions"><button class="maras-rm-btn primary" type="submit">Validate and add mapping</button><button class="maras-rm-btn" type="button" id="maras-rm-export">Export mappings JSON</button><button class="maras-rm-btn" type="button" id="maras-rm-reset">Clear form</button></div></form>' +
    '<div id="maras-rm-status" class="maras-rm-status" aria-live="polite">No mapping validated yet.</div><div class="maras-rm-section">Current session mappings</div><div id="maras-rm-list" class="maras-rm-list"><p>No mappings added yet.</p></div></div></section>';
  document.body.appendChild(overlay);

  var launch = document.createElement('button');
  launch.id = 'maras-rm-launch'; launch.type = 'button'; launch.textContent = 'Requirements Mapper';
  launch.setAttribute('aria-haspopup','dialog'); document.body.appendChild(launch);

  function renderList() {
    var target = $('maras-rm-list');
    if (!records.length) { target.innerHTML = '<p>No mappings added yet.</p>'; return; }
    target.innerHTML = records.slice().reverse().map(function (r) {
      return '<article class="maras-rm-item"><h4>' + esc(r.mappingId) + ' · ' + esc(r.pbi.title) + ' (' + esc(r.validation.decision) + ')</h4>' +
        '<p><b>Trace:</b> ' + esc(r.source.sourceId) + ' / ' + esc(r.source.clauseId) + ' → ' + esc(r.system.finding) + ' → ' + esc(r.mappingId) + '</p>' +
        '<p><b>Requirement:</b> ' + esc(r.requirement) + '</p><p><b>Blockers:</b> ' + esc(r.validation.blockers.length ? r.validation.blockers.join('; ') : 'Completeness checks passed; independent SME verification remains mandatory.') + '</p></article>';
    }).join('');
  }
  function open() { overlay.style.display = 'flex'; $('maras-rm-source-id').focus(); }
  function close() { overlay.style.display = 'none'; launch.focus(); }
  launch.addEventListener('click', open);
  $('maras-rm-close').addEventListener('click', close);
  overlay.addEventListener('click', function (event) { if (event.target === overlay) close(); });
  document.addEventListener('keydown', function (event) { if (event.key === 'Escape' && overlay.style.display === 'flex') close(); });
  $('maras-rm-captured-at').value = new Date().toISOString().slice(0,10);
  $('maras-rm-form').addEventListener('submit', function (event) {
    event.preventDefault();
    var rec = buildRecord(); records.push(rec);
    var status = $('maras-rm-status');
    status.className = 'maras-rm-status ' + (rec.validation.releaseReady ? 'ready' : 'blocked');
    status.innerHTML = '<b>' + esc(rec.validation.decision) + '</b><p>' + esc(rec.validation.note) + '</p><p>' +
      esc(rec.validation.blockers.length ? rec.validation.blockers.join(' · ') : 'Completeness checks passed. Independent source, interpretation, system-evidence and QA/SME review remain mandatory.') + '</p>';
    renderList();
  });
  $('maras-rm-export').addEventListener('click', function () {
    var payload = {schemaVersion:'maras.requirements-mapping.export.v1',exportedAt:new Date().toISOString(),
      warning:'Draft-only data. Browser validation is not proof of compliance or an electronic signature.',mappings:records};
    var blob = new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});
    var url = URL.createObjectURL(blob); var a = document.createElement('a');
    a.href = url; a.download = 'maras-requirements-mappings-draft.json'; a.click();
    setTimeout(function () { URL.revokeObjectURL(url); },1000);
  });
  $('maras-rm-reset').addEventListener('click', function () {
    $('maras-rm-form').reset(); $('maras-rm-captured-at').value = new Date().toISOString().slice(0,10);
  });
  window.MARASRequirementsMapper = {schemaVersion:'maras.requirements-mapping.v1',validate:validate,
    getSessionMappings:function () { return records.map(function (r) { return JSON.parse(JSON.stringify(r)); }); }};
})();
# Regulatory Library Group Checkboxes — Archived Backup

**Archived:** 2026-08-07  
**Removed from:** `index.html` (MARAS v6.3.1 sidebar)  
**Reason:** UI simplified — regulatory source opt-in/opt-out is handled via the expandable tree and header All/None controls.

## How to restore

1. Re-insert the **CSS** block below into `index.html` after `.sb-count{...}`.
2. Re-insert the **HTML** block below into the sidebar, after `#sb-count` and before `#tree`.
3. Re-insert the **JavaScript** block after `dismissOnboardGuide()` and before `buildReqExamples()`.
4. In `init()`, add `buildLibraryChecklist();` before `buildTree()`.
5. In `toggleItem()`, `selAll()`, and `applyFramework()`, add `buildLibraryChecklist();` after `updateCount()`.
6. Update onboarding step 1 to mention Regulatory Library checkboxes.

## Group labels (maps 1:1 to `TREE_DATA` group ids)

```javascript
const REG_LIBRARY_CHECK_LABELS={
  cfr:'US 21 CFR — FDA Regulations',
  eugmp:'EU GMP — EMA Regulations',
  ich:'ICH Guidelines',
  md:'Medical Devices',
  val:'Validation Lifecycle (CSV/CSA)',
  qms:'Quality System & CAPA',
  di:'Data Integrity',
  natl_access:'Access Consortium (Harmonised)',
  natl_apac:'Asia-Pacific Regulators',
  natl_brics:'BRICS & Emerging Markets',
  natl_latam:'LATAM',
  natl_africa:'Africa & Middle East',
  priv:'Privacy, Security & Cloud',
  nongxp:'Non GxP',
};
```

## CSS

```css
.sb-lib-check{padding:8px 10px;border-bottom:1px solid var(--bg2);flex-shrink:0;background:#fafbfc}
.sb-ql-row{display:flex;align-items:center;gap:4px;margin-bottom:4px}
.sb-ql{font-size:10px;font-weight:700;color:var(--ink);text-transform:uppercase;letter-spacing:.4px;flex:1}
.sb-ql-sub{font-size:9px;color:var(--ink4);margin-bottom:6px;line-height:1.35}
.sb-qcheck-actions{display:flex;gap:3px}
.sb-qcheck-btn{font-size:9px;padding:2px 7px;border-radius:8px;border:1px solid var(--border);background:#fff;color:var(--ink3);cursor:pointer;font-family:inherit;font-weight:600}
.sb-qcheck-btn:hover{border-color:var(--blue);color:var(--blue)}
.sb-qcheck-box{border:1px solid var(--border2);border-radius:var(--r);background:#fff;padding:4px;margin-bottom:4px}
.sb-qchecks{display:flex;flex-direction:column;gap:2px}
.qcheck{display:flex;align-items:flex-start;gap:8px;padding:6px 8px;border-radius:var(--r);cursor:pointer;transition:background .12s;border:1px solid transparent}
.qcheck:hover{background:var(--bg)}
.qcheck.on{background:var(--blue-t);border-color:rgba(29,111,206,.25)}
.qcheck-native{width:16px;height:16px;flex-shrink:0;cursor:pointer;accent-color:var(--blue);margin:2px 0 0 0}
.qcheck-lbl{font-size:11px;color:var(--ink);line-height:1.3;cursor:pointer;user-select:none;flex:1}
.qcheck.on .qcheck-lbl{color:var(--blue);font-weight:600}
.qcheck-count{font-size:9px;color:var(--ink4);margin-left:auto;flex-shrink:0;padding-top:2px}
.qcheck.on .qcheck-count{color:var(--blue)}
```

## HTML

```html
  <div class="sb-lib-check">
    <div class="sb-ql-row">
      <span class="sb-ql">Regulatory Library</span>
      <div class="sb-qcheck-actions">
        <button class="sb-qcheck-btn" type="button" onclick="libraryCheckAll(true)">All</button>
        <button class="sb-qcheck-btn" type="button" onclick="libraryCheckAll(false)">None</button>
      </div>
    </div>
    <div class="sb-ql-sub">Select one or more sources — check to opt in, uncheck to opt out</div>
    <div class="sb-qcheck-box">
      <div class="sb-qchecks" id="lib-checks"></div>
    </div>
  </div>
```

## JavaScript

```javascript
/* Display labels for regulatory library group checkboxes (maps 1:1 to TREE_DATA groups) */
const REG_LIBRARY_CHECK_LABELS={
  cfr:'US 21 CFR — FDA Regulations',
  eugmp:'EU GMP — EMA Regulations',
  ich:'ICH Guidelines',
  md:'Medical Devices',
  val:'Validation Lifecycle (CSV/CSA)',
  qms:'Quality System & CAPA',
  di:'Data Integrity',
  natl_access:'Access Consortium (Harmonised)',
  natl_apac:'Asia-Pacific Regulators',
  natl_brics:'BRICS & Emerging Markets',
  natl_latam:'LATAM',
  natl_africa:'Africa & Middle East',
  priv:'Privacy, Security & Cloud',
  nongxp:'Non GxP',
};

/* ─── REGULATORY LIBRARY GROUP CHECKBOXES (opt in / opt out) ────── */
const LIBRARY_GROUP_ORDER=Object.keys(REG_LIBRARY_CHECK_LABELS);

function getGroupItemIds(groupId){
  const g=TREE_DATA.find(x=>x.id===groupId);
  return g?g.items.map(it=>it.id):[];
}
function isLibraryGroupChecked(groupId){
  const ids=getGroupItemIds(groupId);
  return ids.length>0 && ids.every(id=>selItems.has(id));
}
function buildLibraryChecklist(){
  const el=document.getElementById('lib-checks');
  if(!el)return;
  el.innerHTML=LIBRARY_GROUP_ORDER.map(groupId=>{
    const lbl=REG_LIBRARY_CHECK_LABELS[groupId]||groupId;
    const ids=getGroupItemIds(groupId);
    const on=isLibraryGroupChecked(groupId);
    const cnt=ids.filter(id=>selItems.has(id)).length;
    const countTxt=ids.length?`${cnt}/${ids.length}`:'';
    return`<label class="qcheck${on?' on':''}">
      <input type="checkbox" class="qcheck-native" ${on?'checked':''} onchange="toggleLibraryGroup('${groupId}')">
      <span class="qcheck-lbl">${lbl}</span>
      <span class="qcheck-count">${countTxt}</span>
    </label>`;
  }).join('');
}
function toggleLibraryGroup(groupId){
  const ids=getGroupItemIds(groupId);
  const turningOn=!isLibraryGroupChecked(groupId);
  if(turningOn) ids.forEach(id=>selItems.add(id));
  else ids.forEach(id=>selItems.delete(id));
  renderTree();updateCount();buildLibraryChecklist();
}
function libraryCheckAll(on){
  if(on) TREE_DATA.forEach(g=>g.items.forEach(it=>selItems.add(it.id)));
  else selItems.clear();
  renderTree();updateCount();buildLibraryChecklist();
}
```

## Behaviour summary

- 14 group-level checkboxes mapped to `TREE_DATA` top-level groups.
- Checking a group selects all items in that group; unchecking removes them.
- Partial selection shows as unchecked with `n/total` count.
- Synced with tree item toggles and `applyFramework()` presets.

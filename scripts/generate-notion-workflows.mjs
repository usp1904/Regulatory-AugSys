#!/usr/bin/env node
/**
 * Generate Notion-importable Markdown from docs/workflows/platform-workflows.json.
 * Run: node scripts/generate-notion-workflows.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(root, '..');
const registryPath = path.join(repoRoot, 'docs/workflows/platform-workflows.json');
const outDir = path.join(repoRoot, 'docs/workflows/notion-export');

const registry = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });

const indexLines = [
  '# MARAS Workflow Index',
  '',
  `Schema: ${registry.schemaVersion}`,
  `Harness: ${registry.harnessMode} (${registry.pillars.join(' + ')})`,
  '',
  '| ID | Workflow | Graph | MVP |',
  '|----|----------|-------|-----|',
];

for (const wf of registry.workflows) {
  const slug = wf.id.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const filename = `${slug}.md`;
  const mvp = (wf.mvpIds || []).join(', ');
  indexLines.push(`| ${wf.id} | ${wf.name} | ${wf.graph} | ${mvp} |`);

  const sections = [
    `# ${wf.name}`,
    '',
    `**Workflow ID:** ${wf.id}`,
    `**Graph:** ${wf.graph}`,
    '',
    '## MVP traceability',
    '',
    ...(wf.mvpIds || []).map((id) => `- ${id}`),
    '',
  ];

  if (wf.harness) {
    sections.push('## Harness (token optimization)', '', `- ${wf.harness}`, '');
  }
  if (wf.tokenRules?.length) {
    sections.push('## Token rules', '', ...wf.tokenRules.map((r) => `- ${r}`), '');
  }
  if (wf.api?.length) {
    sections.push('## API', '', ...wf.api.map((r) => `- \`${r}\``), '');
  }
  if (wf.web?.length) {
    sections.push('## Web routes', '', ...wf.web.map((r) => `- \`${r}\``), '');
  }
  if (wf.formats?.length) {
    sections.push('## Export formats', '', ...wf.formats.map((f) => `- ${f}`), '');
  }
  if (wf.rules?.length) {
    sections.push('## Business rules', '', ...wf.rules.map((r) => `- ${r}`), '');
  }
  sections.push('## Verification', '', ...(wf.verification || []).map((v) => `- \`${v}\``), '');

  fs.writeFileSync(path.join(outDir, filename), sections.join('\n'));
}

fs.writeFileSync(path.join(outDir, '00-index.md'), indexLines.join('\n'));
console.log(`Generated ${registry.workflows.length + 1} Notion pages in docs/workflows/notion-export/`);

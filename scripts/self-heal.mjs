#!/usr/bin/env node
/**
 * Apply safe auto-fixes, then verify. For Cloud Agents before commit/push.
 * Usage:
 *   node scripts/self-heal.mjs          # fix + verify
 *   node scripts/self-heal.mjs --check  # verify only (CI mode)
 */
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const checkOnly = process.argv.includes('--check');

function run(label, command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || root,
    stdio: 'inherit',
    shell: false,
  });
  if (result.status !== 0) {
    console.error(`\n✗ ${label} failed (exit ${result.status})`);
    process.exit(result.status || 1);
  }
  console.log(`✓ ${label}`);
}

console.log(checkOnly ? 'Self-heal check (no auto-fix)\n' : 'Self-heal: applying safe fixes\n');

if (!checkOnly) {
  run('Ruff auto-fix', 'ruff', ['check', '--fix', '.'], { cwd: path.join(root, 'apps/api') });
  run('Regenerate Notion workflows', 'node', ['scripts/generate-notion-workflows.mjs']);
}

run('Full verification', 'node', ['scripts/verify-all.mjs']);

console.log('\nSelf-heal complete.');

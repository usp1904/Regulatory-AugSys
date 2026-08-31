#!/usr/bin/env node
/**
 * Run all repository verification gates (git-only, no local setup required).
 * Usage: node scripts/verify-all.mjs
 */
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

function run(label, command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || root,
    stdio: 'inherit',
    shell: false,
    env: process.env,
  });
  if (result.status !== 0) {
    console.error(`\n✗ ${label} failed (exit ${result.status})`);
    process.exit(result.status || 1);
  }
  console.log(`✓ ${label}`);
}

console.log('Regulatory-AugSys verify-all\n');

run('MVP regression (p0)', 'node', ['p0-regression.mjs']);
run('QC compatibility regression', 'node', ['qc-compat-regression.mjs']);
run('Notion workflow generation', 'node', ['scripts/generate-notion-workflows.mjs']);
run('API lint (ruff)', 'ruff', ['check', '.'], { cwd: path.join(root, 'apps/api') });
run('API tests (pytest)', 'python', ['-m', 'pytest', '-q'], { cwd: path.join(root, 'apps/api') });
run('Web typecheck', 'npm', ['run', 'typecheck'], { cwd: path.join(root, 'apps/web') });
run('Web lint', 'npm', ['run', 'lint'], { cwd: path.join(root, 'apps/web') });
run('Web build', 'npm', ['run', 'build'], { cwd: path.join(root, 'apps/web') });

console.log('\nAll verification gates passed.');

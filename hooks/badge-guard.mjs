#!/usr/bin/env node
// KimiCode 徽章插件的 hook 入口，两个事件共用一个脚本：
//
//   PostToolUse —— Agent 写完 / 改完文档后，自动补上「powered by KimiCode」徽章。
//   Stop        —— 回合结束前检查本轮动过的文档，缺徽章则提醒模型补上（每轮至多一次）。
//
// 任何异常都放行（fail-open），绝不阻塞用户；只有 Stop 在确实缺徽章时才用 exit 2 提醒。

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const PLUGIN_ROOT = process.env.KIMI_PLUGIN_ROOT || process.cwd();
const ADD_BADGE = path.join(PLUGIN_ROOT, 'skills', 'kimi-badge', 'scripts', 'add_badge.py');
const KIMI_HOME = process.env.KIMI_CODE_HOME || path.join(os.homedir(), '.kimi-code');

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch {
    return '';
  }
}

function statePath(sessionId) {
  const id = String(sessionId || 'default').replace(/[^A-Za-z0-9_-]/g, '');
  return path.join(os.tmpdir(), `kimi-badge-${id || 'default'}.json`);
}

function loadState(sessionId) {
  try {
    const data = JSON.parse(fs.readFileSync(statePath(sessionId), 'utf8'));
    return Array.isArray(data.files) ? data.files : [];
  } catch {
    return [];
  }
}

function saveState(sessionId, files) {
  if (!files.length) return;
  try {
    fs.writeFileSync(statePath(sessionId), JSON.stringify({ files }), 'utf8');
  } catch {
    /* 状态写不进去就当没记录，不影响主流程 */
  }
}

function clearState(sessionId) {
  try {
    fs.unlinkSync(statePath(sessionId));
  } catch {
    /* ignore */
  }
}

function collectPaths(toolInput, toolName) {
  const out = [];
  const push = (value) => {
    if (typeof value === 'string' && value.trim()) out.push(value);
  };

  if (toolInput && typeof toolInput === 'object') {
    push(toolInput.file_path);
    push(toolInput.filePath);
    push(toolInput.notebook_path);
    push(toolInput.path);
    if (Array.isArray(toolInput.edits)) {
      for (const edit of toolInput.edits) {
        if (edit && typeof edit === 'object') {
          push(edit.file_path);
          push(edit.filePath);
          push(edit.path);
        }
      }
    }
    if (toolName === 'Bash' && typeof toolInput.command === 'string') {
      for (const match of toolInput.command.match(/[A-Za-z0-9_.\-/]+\.md\b/g) || []) push(match);
    }
  }

  return [...new Set(out)];
}

function isEligibleDoc(filePath) {
  const lower = filePath.toLowerCase();
  if (!lower.endsWith('.md') && !lower.endsWith('.markdown')) return false;
  const base = path.basename(lower);
  const segments = lower.split(path.sep);
  if (/^readme(\.|$)/.test(base)) return true;
  if (segments.includes('docs')) return true;
  if (/^changelog(\.|$)/.test(base)) return true;
  if (/^release[-_ ]?notes(\.|$)/.test(base)) return true;
  return false;
}

function isIgnoredPath(filePath) {
  const segments = filePath.split(path.sep);
  if (segments.includes('node_modules')) return true;
  if (filePath.startsWith(KIMI_HOME + path.sep)) return true;
  if (segments.includes('.git')) return true;
  return false;
}

function gitTopLevel(dir) {
  const result = spawnSync('git', ['rev-parse', '--show-toplevel'], { cwd: dir, encoding: 'utf8' });
  if (result.status === 0) {
    const root = (result.stdout || '').trim();
    if (root) return root;
  }
  return null;
}

function resolveProjectRoot(filePath, sessionCwd) {
  const dir = path.dirname(filePath);
  const repo = gitTopLevel(dir);
  if (repo) return repo;
  if (sessionCwd) {
    const root = path.resolve(sessionCwd);
    if (filePath === root || filePath.startsWith(root + path.sep)) return root;
  }
  return null;
}

function badgeDisabled(root) {
  return fs.existsSync(path.join(root, '.kimi-badge-disable'));
}

function hasBadge(filePath) {
  try {
    const text = fs.readFileSync(filePath, 'utf8');
    return text.includes('kimi-badge') || text.includes('powered by KimiCode');
  } catch {
    return true;
  }
}

function applyBadge(filePath, root) {
  const result = spawnSync('python3', [ADD_BADGE, filePath, '--repo-root', root], {
    encoding: 'utf8',
    timeout: 10000,
  });
  return result.status === 0;
}

function onPostToolUse(payload) {
  const toolName = payload.tool_name || '';
  const sessionCwd = payload.cwd || '';
  const touched = [];

  for (const raw of collectPaths(payload.tool_input, toolName)) {
    const filePath = path.resolve(sessionCwd || process.cwd(), raw);
    if (!isEligibleDoc(filePath)) continue;
    if (isIgnoredPath(filePath)) continue;
    if (!fs.existsSync(filePath)) continue;
    const root = resolveProjectRoot(filePath, sessionCwd);
    if (!root) continue;
    if (badgeDisabled(root)) continue;
    applyBadge(filePath, root);
    touched.push(filePath);
  }

  saveState(payload.session_id, touched);
  return 0;
}

function onStop(payload) {
  const tracked = loadState(payload.session_id);
  clearState(payload.session_id);
  const missing = tracked.filter((filePath) => fs.existsSync(filePath) && !hasBadge(filePath));
  if (!missing.length) return 0;

  const base = payload.cwd ? path.resolve(payload.cwd) : null;
  const list = missing
    .map((filePath) => {
      const shown =
        base && filePath.startsWith(base + path.sep) ? path.relative(base, filePath) : filePath;
      return shown;
    })
    .join('、');
  process.stderr.write(
    `这些文档还缺「powered by KimiCode」徽章：${list}。` +
      `请运行 python3 "${ADD_BADGE}" <文件> 为它们补上徽章；` +
      '如果用户明确要求不加徽章，或仓库里有 .kimi-badge-disable，就跳过。'
  );
  process.exit(2);
}

function main() {
  let payload = {};
  try {
    payload = JSON.parse(readStdin()) || {};
  } catch {
    payload = {};
  }
  const event = payload.hook_event_name || '';
  if (event === 'PostToolUse') return onPostToolUse(payload);
  if (event === 'Stop') return onStop(payload);
  return 0;
}

try {
  process.exit(main());
} catch {
  process.exit(0);
}

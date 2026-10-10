const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');

const template = fs.readFileSync('app/templates/transcriber_workspace.html', 'utf8');
const css = fs.readFileSync('app/static/style.css', 'utf8');
const main = fs.readFileSync('app/main.py', 'utf8');

test('transcriber workspace exposes server-counted filters and one-page editor', () => {
  for (const label of ['À transcrire', 'Transcrits', 'Tous']) assert.match(template, new RegExp(label));
  for (const id of ['transcriber-list', 'transcriber-selection', 'editor-audio', 'transcription-form', 'transcriber-search-input', 'next-recording', 'back-to-list']) assert.match(template, new RegExp(`id="${id}"`));
  assert.match(template, /counts\.todo/);
  assert.match(template, /counts\.transcribed/);
  assert.match(template, /counts\.all/);
  assert.match(template, /beforeunload/);
  assert.match(template, /Des modifications non enregistrées seront perdues/);
  assert.match(template, /search\.addEventListener\('input'/);
  assert.match(template, /selectNext\(\)/);
});

test('transcriber workspace stays scoped and responsive', () => {
  assert.match(css, /\.transcriber-workspace\{display:grid;grid-template-columns:minmax\(18rem,24rem\) minmax\(0,1fr\)/);
  assert.match(css, /@media\(max-width:900px\)\{\.transcriber-workspace\{grid-template-columns:1fr\}/);
  assert.match(css, /\.transcriber-item:hover/);
  assert.match(css, /\.transcriber-filter:hover/);
  assert.match(css, /\.transcriber-search/);
  assert.match(css, /\.transcriber-editor-actions/);
});

test('only transcribers receive the workspace branch and save keeps the workflow', () => {
  assert.match(main, /if user\.role == "TRANSCRIBER":\s+active_filter = request\.query_params\.get\("filter", "todo"\)/);
  assert.match(main, /RedirectResponse\(f"\/recordings\?filter=todo&selected=\{next_recording\.id\}&saved=1"/);
  assert.match(main, /user=require\(request,db,\["ADMIN","PARTICIPANT","TRANSCRIBER"\]\)/);
});

console.log('transcriber workspace checks passed');

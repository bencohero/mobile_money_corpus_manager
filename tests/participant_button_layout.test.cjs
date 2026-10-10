const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');

const template = fs.readFileSync('app/templates/participant_record.html', 'utf8');
const css = fs.readFileSync('app/static/style.css', 'utf8');

test('participant recording actions keep stable ids and semantic variants', () => {
  for (const id of ['start', 'stop', 'play-recording', 'cancel', 'upload', 'next-phrase', 'another-take', 'success-actions', 'preview']) {
    assert.match(template, new RegExp(`id="${id}"`));
  }
  assert.match(template, /participant-actions--start/);
  assert.match(template, /participant-actions--recording/);
  assert.match(template, /participant-actions--review/);
  assert.match(template, /participant-button--primary/);
  assert.match(template, /participant-button--secondary/);
  assert.match(template, /participant-button--stop/);
  assert.match(template, /id="start"[\s\S]*?Commencer l’enregistrement/);
  assert.match(template, /id="stop"[\s\S]*?Arrêter/);
  assert.match(template, /id="play-recording"[\s\S]*?Écouter/);
  assert.match(template, /id="cancel"[\s\S]*?Recommencer/);
  assert.match(template, /id="upload"[\s\S]*?Envoyer mon enregistrement/);
  assert.match(template, /id="success-actions"[\s\S]*?Enregistrement envoyé/);
  assert.match(template, /id="another-take"[\s\S]*?Faire une autre prise/);
  assert.match(template, /id="next-phrase"[\s\S]*?Passer à la phrase suivante/);
});

test('participant actions define the requested responsive layout and accessible disabled state', () => {
  assert.match(css, /\.participant-actions--review\{[^}]*max-width:46rem/);
  assert.match(css, /@media\(max-width:359px\)\{\.participant-actions__secondary\{grid-template-columns:1fr\}\}/);
  assert.match(css, /@media\(min-width:768px\)\{\.participant-actions--review\{grid-template-columns:minmax\(9rem,1fr\) minmax\(10rem,1fr\) minmax\(15rem,1\.45fr\)/);
  assert.match(css, /\.participant-button\{[^}]*min-height:52px/);
  assert.match(css, /\.participant-button:focus-visible\{[^}]*outline:3px solid/);
  assert.match(css, /\.participant-button:disabled\{[^}]*opacity:1/);
  assert.match(css, /\.participant-recording-card \.participant-button--secondary:hover:not\(:disabled\)\{[^}]*color:#18324a[^}]*background:#fff/);
});

console.log('participant button layout checks passed');

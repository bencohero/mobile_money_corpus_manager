const assert = require('node:assert/strict');
const fs = require('node:fs');

const source = fs.readFileSync('app/static/participant_registration.js', 'utf8');
const template = fs.readFileSync('app/templates/participant_register.html', 'utf8');

assert.match(source, /if \(submitting/);
assert.match(source, /button\.disabled = true/);
assert.match(source, /navigator\.clipboard\.writeText/);
assert.match(source, /password\.value = ""/);
assert.match(source, /response\.text\(\)/);
assert.match(source, /contentType\.includes\("application\/json"\)/);
assert.match(source, /temporairement indisponible/);
assert.doesNotMatch(template, /name="(?:role|username|participant_code|sequence_number|is_active|permissions)"/);
assert.match(template, /label for="workshop-code"/);
assert.match(template, /role="alert"/);
assert.match(template, /href="\/login"/);

console.log('participant registration frontend checks passed');

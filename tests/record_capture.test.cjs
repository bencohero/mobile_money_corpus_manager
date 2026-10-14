const {test} = require('node:test');
const assert = require('node:assert/strict');
const {CaptureState, PreviewSequence} = require('../app/static/record_capture.js');
const fs = require('node:fs');
const vm = require('node:vm');

function browserFixture() {
  const elements = Object.fromEntries(['status','start','stop','upload','cancel','preview','utterance','condition','participant','take','meter','recorder-orb','scenario'].map(id => [id, {
    value: id === 'condition' ? 'CLEAN' : '1', disabled: false, textContent: '',
    style: {}, selectedOptions: [{dataset: {scenario:'Synthetic'}}],
    listeners: {}, addEventListener(event, fn) {this.listeners[event] = fn;},
    parentElement: {setAttribute() {}}, classList: {add() {}, remove() {}},
    removeAttribute() {}, load() {},
  }]));
  const requests = [];
  const sandbox = {RecordingCapture: {CaptureState, PreviewSequence}, document: {getElementById: id => elements[id]},
    fetch: async (url, options) => {requests.push({url,options}); return {ok:true,json:async()=>({next_take_number:7})};},
    crypto: {randomUUID: ()=>'test-capture-key'}, URLSearchParams, Blob,
    URL: {createObjectURL: ()=>'blob:test', revokeObjectURL() {}},
    cancelAnimationFrame() {}, requestAnimationFrame() {return 1;},
    navigator: {mediaDevices:{getUserMedia:async()=>({getTracks:()=>[{stop(){}}]})}},
    MediaRecorder: class {
      static isTypeSupported() {return true;}
      constructor() {sandbox.recorder = this;}
      start() {this.state='recording';}
      stop() {this.state='inactive'; this.ondataavailable({data:new Blob(['audio'])});this.onstop();}
    },
    AudioContext: class {
      createAnalyser() {return {frequencyBinCount:1,getByteFrequencyData(){}};}
      createMediaStreamSource() {return {connect(){}};}
      close() {}
    },
    Uint8Array,
  };
  // CaptureState's default factory resolves crypto in its own Node module.
  sandbox.RecordingCapture.CaptureState = class extends CaptureState {constructor(){super(()=> 'test-capture-key');}};
  vm.createContext(sandbox);
  const html = fs.readFileSync('app/templates/record.html','utf8');
  const script = html.match(/<script[^>]*nonce=[^>]*>\s*([\s\S]*?)<\/script>/)[1];
  vm.runInContext(script, sandbox);
  return {elements, requests, sandbox};
}

test('capture freezes its business key and keeps its idempotency key across retries', () => {
  const state = new CaptureState(() => 'key-one');
  const selection = {participant_id: '1', utterance_id: '2', condition: 'CLEAN'};
  state.begin(selection);
  selection.utterance_id = '3';
  state.recorded({size: 10});
  const first = state.submission();
  assert.equal(first.utterance_id, '2');
  assert.equal(first.idempotency_key, 'key-one');
  assert.equal(state.submission(), null);
  state.retry();
  assert.deepEqual(state.submission(), first);
  state.completed();
  assert.equal(state.locked, false);
});

test('an old preview response cannot replace the current selection', async () => {
  const pending = [];
  const preview = new PreviewSequence(params => new Promise(resolve => pending.push(resolve)));
  const results = [];
  const a = preview.refresh({utterance_id: 1}, value => results.push(value));
  const b = preview.refresh({utterance_id: 2}, value => results.push(value));
  pending[1]({next_take_number: 1}); await b;
  pending[0]({next_take_number: 8}); await a;
  assert.deepEqual(results, [{next_take_number: 1}]);
});

test('actual page requests the complete key on load and each selection change', async () => {
  const {elements,requests} = browserFixture();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(elements.take.textContent, 'Prise estimée 7');
  for (const [id,value] of [['utterance','2'],['condition','NOISY'],['participant','3']]) {
    elements[id].value=value; elements[id].listeners.change();
    await new Promise(resolve=>setImmediate(resolve));
    const url = new URL(requests.at(-1).url, 'http://test');
    assert.equal(url.searchParams.get(id === 'condition' ? id : id+'_id'), value);
  }
  assert.equal(requests.length,4);
});

test('actual capture locks all selectors until cancellation, including after stop', async () => {
  const {elements} = browserFixture();
  await elements.start.onclick();
  for (const id of ['participant','utterance','condition']) assert.equal(elements[id].disabled,true);
  elements.stop.onclick();
  for (const id of ['participant','utterance','condition']) assert.equal(elements[id].disabled,true);
  elements.cancel.onclick();
  for (const id of ['participant','utterance','condition']) assert.equal(elements[id].disabled,false);
});

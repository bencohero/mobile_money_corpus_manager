/* Capture state shared by the browser and dependency-free Node tests. */
(function (root) {
  class CaptureState {
    constructor(keyFactory = () => crypto.randomUUID()) { this.keyFactory = keyFactory; this.completed(); }
    begin(selection) {
      if (this.locked) throw new Error('Une capture est déjà active.');
      this.selection = Object.freeze({...selection});
      this.key = this.keyFactory(); this.locked = true;
    }
    recorded(blob) { this.blob = blob; }
    submission() {
      if (!this.blob || this.sending) return null;
      this.sending = true;
      return {...this.selection, idempotency_key: this.key};
    }
    retry() { this.sending = false; }
    completed() { this.selection = null; this.blob = null; this.key = null; this.locked = false; this.sending = false; }
  }
  class PreviewSequence {
    constructor(fetcher) { this.fetcher = fetcher; this.generation = 0; }
    async refresh(selection, accept) {
      const current = ++this.generation;
      try {
        const value = await this.fetcher(selection);
        if (current === this.generation) accept(value);
      } catch (error) { if (current === this.generation) accept({error: error.message}); }
    }
  }
  const api = {CaptureState, PreviewSequence};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.RecordingCapture = api;
})(globalThis);

# G8.6-R — Validation export

Export demandé par l’interface admin avec `workshop_id=6`, mode `work`,
`strict=true`. Réponse HTTP 200.

Archive observée : `mobile_money_corpus_20261013T021119Z.zip`  
SHA-256 de l’archive :
`e4ee6ba478f964dd34aa134fb23c00c31e52c02ca5e9f00e8cfcd0820a0b7568`.

Validation ZIP : PASS. Huit entrées présentes : trois WAV, `recordings.csv`,
`metadata.csv`, `manifest.json`, `recordings.jsonl` et `SHA256SUMS`.

Le manifest et `SHA256SUMS` sont présents et cohérents ; les trois fichiers
audio correspondent exclusivement aux recordings 16–18 de l’atelier 6.

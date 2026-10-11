# F.5A.1 — Évaluation de cohérence des écritures

## Verdict

**BLOQUÉ pour une sauvegarde coordonnée sans correction préalable.**

La base et MinIO sont réconciliables à l’instant T, mais le code ne fournit pas de barrière commune entre les deux systèmes.

Une dérive de schéma est également ouverte : la base est à `0005_workshop_attribution`, tandis que les migrations du dépôt vont jusqu’à `0008`; `transcription_history`, `participant_language_sequences` et `rate_limit_buckets` sont absentes du schéma observé. Il ne faut pas appliquer ces migrations dans le cadre d’une sauvegarde. Leur plan de résolution doit être séparé et validé avant de conclure que tous les chemins applicatifs sont couverts.

## Chemins d’écriture étudiés

- Inscription : route `POST /api/auth/participant-registration`, compteur de langue verrouillé en base, participant/utilisateur/receipt/audit dans la transaction.
- Prise audio : `POST /api/recordings`, réservation idempotente, écriture raw et WAV dans MinIO, vérification taille/checksum, puis publication `READY` en PostgreSQL avec compensations en cas d’échec.
- Compteurs : `app/take_sequence.py` et table `recording_take_counters`, utilisés lors de la réservation.
- Soumissions : `app/recording_submission.py`, receipt idempotent et état de soumission en base.
- Transcription : `POST /transcribe/{recording_id}`, écriture ou mise à jour de `transcriptions` et historique.
- Vérification : `POST /verify/{recording_id}`, mise à jour optimiste de transcription, statut et historique.
- Réconciliation : `scripts/reconcile.py`, lecture seule ; détecte objets manquants/orphelins, divergences de taille/checksum et états intermédiaires.
- Asynchrone : aucun worker/queue séparé trouvé dans Compose ou le code ; le traitement audio est synchrone dans le chemin HTTP.

## Ce qui est démontré

- Réconciliation actuelle : code 0, aucun finding.
- 15/15 enregistrements ont les deux objets et leurs métadonnées de taille/checksum.
- 15/15 sont `READY` ; 15/15 ont une soumission et un compteur compatible.
- Les contraintes et compensations réduisent les orphelins lors d’un flux normal.

## Ce qui n’est pas démontré

- Que toutes les requêtes d’écriture sont terminées au début du dump PostgreSQL.
- Que plus aucun upload, transcription, vérification ou audit ne survient pendant le miroir MinIO.
- Que l’arrêt du conteneur `app` laisse terminer chaque requête en vol ; aucun mécanisme de drain ni timeout contractuel n’est configuré.
- Que Traefik cesse d’acheminer avant la capture ; aucun mode maintenance n’a été activé ni vérifié.
- Que les chemins dépendant des migrations `0006` à `0008` fonctionnent avec le schéma actif.

## Correction minimale

Avant toute capture : introduire une fenêtre de maintenance validée qui bloque les nouvelles écritures au niveau de l’application ou de l’entrée, observe un drain explicite (requêtes en vol = 0, traitement audio = 0, file asynchrone = 0 si elle existe), puis capture PostgreSQL et MinIO sans réactiver l’application. La reprise doit être séparée et contrôlée par un opérateur. Si cette barrière ne peut pas être ajoutée ou démontrée, seule une sauvegarde séparée « best effort » est possible et elle doit être signalée comme incomplète, pas comme cohérente.

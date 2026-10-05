# Export ZIP du corpus

L’export complet est réservé au rôle `ADMIN`. L’interface est disponible sur `/admin/export` et le téléchargement est un `POST /admin/export/corpus` protégé par le même cookie/session et le même jeton CSRF que les autres formulaires.

Paramètres validés : `mode=work|benchmark`, `status`, `verification_status`, `condition=CLEAN|NOISY`, `participant`, `intent`, `has_transcription=true|false`, `date_min`, `date_max` (`YYYY-MM-DD`) et `strict=true|false`. Le mode `work` inclut les prises correspondant aux filtres, même non vérifiées. Le mode `benchmark` exige `status=VERIFIED`, `verification_status=VERIFIED`, une transcription de référence, un objet WAV présent, lisible et PCM signé 16 bits mono 16 kHz. `strict=true` est la valeur de l’interface : toute anomalie échoue avant qu’une archive soit annoncée. Avec `strict=false`, l’entrée est exclue et sa cause est comptée dans le manifeste.

Structure produite :

```text
mobile_money_corpus_<UTC timestamp>/
├── metadata/recordings.csv       # schéma administratif minimal demandé
├── metadata/metadata.csv         # colonnes compatibles benchmark/Colab
├── metadata/manifest.json
├── metadata/recordings.jsonl     # valeurs textuelles brutes sûres pour préserver la transcription
├── audio/clean/<audio_id>.wav
├── audio/noisy/<audio_id>.wav
└── SHA256SUMS
```

Les statistiques du manifeste sont calculées à partir des WAV réellement écrits. `recordings.csv` contient `audio_id`, `file_name`, `relative_audio_path`, participant, intention, condition, prise, statuts, transcription, propriétés WAV, taille et SHA-256. `metadata.csv` fournit les correspondances `speaker_id`, `environment`, `duration_sec`, `reference_text`, `intent_expected`, `validation_status`, etc.; les champs indisponibles restent vides. Les identifiants source comme `mos_0001` et `MOS_003` ne sont pas renommés.

Les fichiers MinIO sont lus par blocs de 1 MiB, copiés temporairement pour permettre la validation `wave`, puis empaquetés. L’archive est construite dans un fichier temporaire contrôlé et streamée; elle est supprimée après succès, exception ou interruption. Limites : 10 000 enregistrements et 20 GiB estimés; le quota disque temporaire doit couvrir au plus un WAV temporaire par prise en cours et l’archive finale. Aucun FFmpeg n’est exécuté pendant l’export. Les réponses utilisent `Cache-Control: no-store` et `X-Content-Type-Options: nosniff`.

Les erreurs sont classifiées au minimum en `db_without_object`, `object_not_found`, `storage_timeout`, `storage_permission_denied`, `storage_unavailable`, `checksum_mismatch`, `invalid_wav`, `missing_transcription`, `not_verified` et `duplicate_archive_path`. Les logs structurés contiennent l’identifiant administrateur, le mode, les filtres et le résultat, sans transcription, cookie, token, endpoint ni chemin temporaire. L’export ne modifie ni PostgreSQL ni MinIO; le journal d’audit existant n’est pas écrit afin de préserver cette garantie de lecture seule.

Pour prévenir l’injection dans un tableur, les cellules CSV commençant par `=`, `+`, `-` ou `@` reçoivent une apostrophe. La transcription exacte reste disponible dans `metadata/recordings.jsonl`; un pipeline benchmark qui exige la valeur brute doit lire ce fichier ou retirer uniquement l’apostrophe de protection après validation de provenance.

Procédure benchmark :

1. Télécharger le ZIP depuis l’administration.
2. Vérifier `SHA256SUMS`, par exemple avec `sha256sum -c SHA256SUMS` depuis le répertoire racine de l’export.
3. Extraire l’archive.
4. Copier `audio/clean` et `audio/noisy` dans le benchmark.
5. Copier `metadata/metadata.csv`.
6. Exécuter les contrôles audio.
7. Lancer le notebook.

Exemple sans secret : ouvrir `/admin/export`, choisir `benchmark`, conserver `strict=true`, puis télécharger le fichier proposé. Les téléchargements directs MinIO et les URLs présignées ne sont jamais exposés.

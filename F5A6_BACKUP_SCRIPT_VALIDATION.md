# F5A6 — validation du script

Script livré : [scripts/backup_local.sh](scripts/backup_local.sh). Il capture dans `<BACKUP_ID>.incomplete`, puis renomme vers `<BACKUP_ID>` uniquement après succès. Les erreurs conservent l’archive incomplète et ne suppriment aucune donnée source.

Artefacts publiés : `postgres/corpus.dump`, `postgres.list`, `minio/`, `manifests/MANIFEST.json`, `manifests/SHA256SUMS`, `COMPLETE`, `COMPLETION.SHA256`, et `reports/backup_report.json`. Le rapport compare les références `recordings.raw_object/wav_object` aux objets copiés et refuse les manquants ou orphelins.

Validation exécutée :

```text
./tests/test_f5a6_synthetic.sh
F5A6 synthetic guard/capture tests: 10 passed
```

Les scénarios couverts sont : application arrêtée, application absente, application active refusée, attestation absente refusée, session PostgreSQL détectée refusée, dump échoué, copie MinIO échouée, dump tronqué, archive existante et archive complète avec manifestes.

Une preuve de restauration synthétique isolée a aussi été exécutée avec PostgreSQL 16 et deux MinIO éphémères sans volume de production : une ligne SQL et un objet `audio/a.wav` ont été restaurés et vérifiés. Les conteneurs et le réseau temporaires ont été supprimés ensuite. La stack historique `docker-compose.test.yml` n’a pas été utilisée pour la restauration car son volume `db-test` existant échouait sur un checkpoint PostgreSQL invalide.

Contrôles de forme : `bash -n` du script et du test, `docker compose -f docker-compose.test.yml config --quiet`, et `git diff --check` réussissent.

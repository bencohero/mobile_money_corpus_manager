# Remédiation C — rapport d’exécution

## 1. Diagnostic initial

L’audit du dépôt a confirmé que `/audio/{recording_id}` appelait `get_bytes()` et chargeait l’objet WAV complet en mémoire. La liste `/recordings` chargeait toutes les prises puis appliquait les filtres transcripteur en Python. Les filtres de dates, de transcription et de vérification des exports étaient également appliqués après `query.all()`.

La base et MinIO utilisés pour les vérifications sont ceux du compose de test (`db-test` et `minio-test`). Aucun accès à la base ou aux objets de production n’a été effectué.

## 2. Modifications effectuées

- Ajout d’un générateur MinIO `stream_file()` avec lecture par blocs de 1 MiB et fermeture systématique de la réponse.
- `/audio/{recording_id}` retourne désormais `200` en lecture complète, `206` pour une plage valide et `416` pour une plage invalide ou non satisfaisable. Les en-têtes `Accept-Ranges`, `Content-Length`, `Content-Range` et le type MIME sont renseignés.
- Les contrôles d’authentification, d’autorisation participant et d’état `READY` sont conservés.
- Les listes d’enregistrements sont paginées, plafonnées à 100 lignes par page et ordonnées par `(created_at DESC, id DESC)`. Les filtres transcripteur `todo`, `transcribed` et `all` sont calculés en SQL.
- La lecture JSON d’inscription est bornée même sans `Content-Length`, y compris pour un transfert chunked. Le contrôle de taille effective de l’upload audio était déjà effectué pendant la lecture et reste actif.
- Les filtres d’export de transcription, de statut de vérification et de dates sont maintenant poussés dans la requête SQL. Les requêtes SQLAlchemy utilisent `yield_per(100)` quand disponible et refusent explicitement un export au-delà de la limite configurée.

Aucune migration n’a été ajoutée : les index existants couvrent les parcours paginés principaux et une migration de performance n’est pas justifiée sans mesure PostgreSQL représentative.

## 3. Fichiers concernés

- `app/storage.py`
- `app/main.py`
- `app/corpus_export.py`
- `app/templates/transcriber_workspace.html`
- `app/templates/recordings.html`

## 4. Mesures et benchmarks

La référence fonctionnelle disponible avant ce lot était la suite B complète : **147 tests réussis, 1 test ignoré**. Aucun benchmark de production n’a été réalisé.

La vérification ciblée après modification a donné : **16 tests réussis** (`tests/test_remediation_c.py` et `tests/test_corpus_export.py`) et les tests d’export MinIO/PostgreSQL ont conservé leurs formats ZIP, CSV, JSONL, manifestes et empreintes SHA-256.

Les mesures p50/p95, mémoire maximale, débit audio et jeux synthétiques 1 000/10 000/100 000 ne sont pas encore disponibles dans cet environnement. Aucun gain chiffré n’est donc déclaré.

## 5. Résultats et limites

La suite ciblée `tests/test_corpus_export.py tests/test_integration_http.py tests/test_p0a3_negative.py` a produit **20 réussis et 2 échecs**. Les deux échecs sont liés aux fixtures persistantes du compose de test : création d’un participant historique refusée en `400`, puis utilisateur propriétaire ne correspondant plus à l’enregistrement réutilisé et recevant `403`. Ils doivent être isolés par une base de test fraîche avant validation finale.

Le support Range et les limites chunked doivent encore recevoir des tests HTTP dédiés avec un objet MinIO synthétique. La pagination transcripteur conserve la recherche locale sur la page courante ; une recherche SQL globale est une amélioration ultérieure possible.

## 6. Risques résiduels

- La construction ZIP conserve encore des métadonnées intermédiaires jusqu’à la fin de l’export ; un export asynchrone ou un spool disque complet pourra être envisagé après mesures.
- Un téléchargement audio long consomme toujours le temps d’un worker, même si sa mémoire est bornée.
- Les pages de référence peuvent nécessiter une migration de schéma si les benchmarks PostgreSQL démontrent un manque d’index.

## 7. Déploiement et retour arrière sûr

1. Recréer une copie de base de test et vérifier la révision Alembic avant toute opération.
2. Exécuter la suite complète et les benchmarks sur `docker-compose.test.yml`.
3. Déployer l’application avec les mêmes limites de reverse proxy et vérifier `/ready`, Range `206/416`, pagination et exports.
4. Ne lancer aucune migration sur la production pour ce lot en l’absence de migration ajoutée.
5. En cas de régression, revenir au commit applicatif précédent via le mécanisme de déploiement versionné, sans toucher aux données ni aux compteurs.

## Statut

**Lot C non déclaré terminé.** Le streaming, la pagination et le déplacement des filtres SQL sont implémentés, mais la validation finale exige un environnement de test propre, les tests HTTP Range dédiés et les benchmarks reproductibles demandés par le ticket.

---

# Complément C.1 — validation finale

## Environnement isolé et résolution des deux échecs

Les volumes du compose historique sont nommés `mobile-money-corpus-p0a2-test-*`. Ils n’ont pas été supprimés ni réutilisés. C.1 utilise les overlays `docker-compose.c1.test.yml` et `docker-compose.c1b.test.yml`, avec des bases, buckets, volumes et réseaux dédiés (`c1-*` et `c1b-*`). La révision PostgreSQL vérifiée est `0007_integrity_and_transcription_versions`.

| Échec initial | Cause | Correction | Résultat |
|---|---|---|---|
| Création participant HTTP en `400` au second passage | Le test cherchait un code demandé alors que l’API attribue le code public (`MOS_…`) et l’utilisateur existait déjà | Fixture rendue idempotente sur le nom d’utilisateur | Résolu |
| Permission audio `403` sur l’enregistrement global le plus récent | `remaining_recording()` sélectionnait une prise appartenant à un autre participant | Sélection limitée au `participant_id` de `p0a2-participant` | Résolu |

Les tests HTTP ciblés après correction donnent **8 passed**. Aucun skip n’a été ajouté.

## Tests HTTP Range et ressources MinIO

`tests/test_remediation_c.py` couvre un WAV synthétique réellement stocké dans MinIO : lecture complète `200`, plage ouverte, plage suffixe, bornes invalides `416`, plage malformée, plage multiple et ressource inexistante `404`. Les en-têtes et les octets reçus sont comparés exactement. Le générateur MinIO vérifie également la fermeture et la libération de la réponse après lecture.

Résultat : **5 passed**, dont le test HTTP Range complet, l’erreur de stockage `502` et la fermeture après interruption. Les contrôles d’autorisation `403` sont également couverts par les tests de permissions HTTP.

## Pagination, filtres et limites

La pagination conserve l’ordre `(created_at DESC, id DESC)`, plafonne `page_size` à 100 et compte les vues SQL `todo`, `transcribed` et `all`. Les tests B et HTTP de permissions ont été exécutés sur l’environnement propre ; les conflits de transcription et les statuts de vérification restent verts.

Les tests d’inscription et d’upload vérifient les protections CSRF, les formats, les durées et les erreurs de taille. La lecture JSON applicative limite maintenant le corps effectif pour `Content-Length` absent ou transfert chunked. Aucun objet READY partiel n’est conservé lors d’un échec d’upload.

## Benchmarks reproductibles

Outil : `scripts/benchmark_remediation_c.py`. Commande exécutée dans le conteneur `test` :

```text
python scripts/benchmark_remediation_c.py --sizes 1000,10000,100000
```

Conditions : PostgreSQL 16 Alpine dans Docker, application et test sur le même hôte, 6 CPU visibles, environ 11,7 GiB RAM sans swap au moment de la mesure, page de 50 lignes, cinq répétitions par taille, insertion puis suppression des données synthétiques.

| Corpus | Liste p50 | Liste p95 | Count p50 | Count p95 | Requêtes page/count |
|---:|---:|---:|---:|---:|---:|
| 1 000 | 63,017 ms | 128,018 ms | 65,749 ms | 1 137,023 ms | 1 / 1 |
| 10 000 | 64,183 ms | 73,995 ms | 73,305 ms | 89,399 ms | 1 / 1 |
| 100 000 | 106,154 ms | 120,342 ms | 139,947 ms | 165,505 ms | 1 / 1 |

Ces valeurs sont des mesures absolues ; aucune comparaison pré-optimisation équivalente n’est disponible. Le benchmark ne touche pas à la production. Les exports conservent leurs tests de format et d’empreinte, mais aucun gain de durée d’export n’est revendiqué sans jeu MinIO volumineux comparable.

## Suites finales

- Suite Python complète sur environnement C.1B propre, passage 1 : **153 passed, 1 skipped, 2331 warnings**.
- Suite Python complète sur le même environnement, passage 2 : **153 passed, 1 skipped, 2331 warnings**.
- Test Node : **10 passed, 0 failed**.
- `docker compose ... config --quiet` : réussi.
- `bash -n scripts/*.sh` et `git diff --check` : réussis.

Le seul test ignoré est `tests/test_dev_environment.py`, qui indique explicitement que le CLI Docker est absent dans le conteneur de test ; la validation Compose a été exécutée depuis l’hôte. Les avertissements sont principalement des dépréciations `datetime.utcnow`, Starlette `TemplateResponse` et `BlockingPortal`; ils ne masquent aucun échec.

## Statut final

**VALIDÉ — C.1.** Les deux échecs initiaux sont expliqués et corrigés, l’environnement est reproductible et isolé, les tests Range/pagination/permissions/export des lots A et B sont verts, et les deux exécutions complètes sont sans échec. Aucun volume de production n’a été consulté, modifié ou supprimé.

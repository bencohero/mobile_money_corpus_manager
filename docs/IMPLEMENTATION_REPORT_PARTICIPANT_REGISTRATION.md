# Rapport d’implémentation — auto-inscription participant

Date : 2026-10-05

## Cause et besoin métier

La création des comptes participants dépendait entièrement du formulaire administrateur `/participants`, qui demandait séparément un code participant et un nom d’utilisateur. Le nouveau parcours permet une inscription autonome contrôlée par atelier, sans ouvrir la création des rôles privilégiés.

## Architecture retenue

- Identité publique `MOS_NNN`, conforme à `^MOS_[0-9]{3,}$`, allouée exclusivement par `participant_login_number_seq`.
- Valeur identique dans `users.username` et `participants.participant_code` pour préserver l’authentification, les noms audio et les exports existants.
- Relation `User 1 — 0..1 Participant` garantie par la FK existante et une nouvelle contrainte unique sur `users.participant_id`.
- Service `register_participant` responsable de la validation, du verrou atelier, de la réservation, des deux créations, du compteur et de l’audit dans une seule transaction.
- Codes d’atelier stockés uniquement sous empreinte HMAC-SHA-256 avec une clé de production dédiée.
- Route JSON publique protégée par CSRF et limitation de débit, plus une interface mobile sans champs d’identité ou de privilège.
- Administration séparée pour les ateliers et assistance participant, toutes deux limitées au rôle `ADMIN` et auditées.

## Migration

La nouvelle révision `0004_participant_registration` ajoute la séquence, la contrainte 1–1, `workshop_codes`, les contraintes de capacité et les index. Elle calcule le maximum historique dans les deux colonnes d’identité et refuse les liens multiples, les paires divergentes et les alias numériques ambigus. Elle ne renumérote aucune donnée. Son downgrade est bloqué pour éviter la perte du registre et la réutilisation d’identités.

## Concurrence et rollback

`nextval` fournit des numéros distincts, y compris sous concurrence; ses valeurs ne sont pas annulées lors d’un rollback. `SELECT ... FOR UPDATE` sérialise l’utilisation d’un même atelier, notamment sa dernière place. Les contraintes uniques restent la protection finale. Une exception annule compte, fiche, compteur et audit; un trou de séquence reste acceptable.

## Autorisations et secrets

Le payload public est en liste blanche et tout champ tel que `role`, `username`, `participant_code`, `sequence_number`, `is_active`, `is_superuser` ou `permissions` est rejeté. Le service fixe `PARTICIPANT` et un compte actif. Les routes `/users`, `/participants`, `/admin/workshop-codes`, d’assistance et de création privilégiée conservent le contrôle `ADMIN`. Les mots de passe utilisent bcrypt existant; aucun mot de passe ni code atelier n’est renvoyé ou audité.

## Résultats de validation

- Compilation Python : réussie.
- Migration réelle de la base de test `0003` vers `0004` : réussie après correction précoce de la longueur de l’identifiant Alembic; le premier essai avait été intégralement rollbacké par PostgreSQL.
- Initialisation historique `MOS_999` → prochaine valeur `MOS_1000` : réussie.
- Tests ciblés service/migration/concurrence : 31 réussis avant ajout du cas historique, puis cas historique réussi isolément.
- Test HTTP public complet : 1 réussi.
- Régression Python complète : 120 réussis en 160,49 s, aucun échec.
- Contrôle ciblé final après ajout de la clé atelier dédiée : 33 réussis, 4 tests de concurrence désélectionnés car déjà couverts par la régression complète.
- Test frontend Node : réussi.
- Configuration Docker Compose de test : valide.
- `git diff --check` : valide avant contrôle final.

Les avertissements de test sont des dépréciations préexistantes (`datetime.utcnow`, FastAPI `on_event`, ancien ordre `TemplateResponse`, Passlib `crypt`) et ne constituent pas des échecs fonctionnels.

## Vérifications manuelles et risques résiduels

Les contrôles automatisés couvrent le DOM essentiel, le double envoi, l’effacement des mots de passe, la copie, le retour connexion, le CSRF et les permissions. Une validation physique Android/lecteur d’écran reste nécessaire avant ouverture d’atelier. Le limiteur en mémoire doit être complété par Traefik ou un stockage partagé en déploiement multi-processus. Le fuseau des dates atelier est celui du serveur. Le parcours admin historique conserve ses identifiants libres pour compatibilité; le format `MOS_NNN` est garanti par le parcours public.

## Déploiement et retour arrière

Suivre `docs/PARTICIPANT_SELF_REGISTRATION.md` : sauvegarde/restauration vérifiée, configuration de `WORKSHOP_CODE_SECRET`, arrêt des écritures, `alembic upgrade head`, déploiement coordonné puis test d’un atelier limité. Le retour arrière se fait par arrêt des écritures et restauration de la sauvegarde pré-migration; `alembic downgrade` est volontairement refusé.

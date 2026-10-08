# Auto-inscription sécurisée des participants

## Besoin et architecture

Un participant peut créer son compte depuis `/participant/register`, uniquement avec un code d’atelier actif. La route JSON `POST /api/auth/participant-registration` accepte le code, les champs déjà présents dans la fiche participant, le consentement et deux saisies du mot de passe. Les champs d’identité, de rôle, de statut et de permission sont interdits dans le contrat public.

L’identifiant canonique est `MOS_NNN` (`^MOS_[0-9]{3,}$`). PostgreSQL l’attribue avec `participant_login_number_seq`; l’application écrit la même valeur dans `users.username` et `participants.participant_code` au cours d’une transaction unique. Cette copie maintient la compatibilité avec le modèle et les exports existants. La séquence est l’autorité d’attribution et les contraintes uniques PostgreSQL sont l’autorité finale contre les collisions. Les trous dus aux rollbacks sont normaux et les numéros ne sont jamais recyclés.

La transaction verrouille la ligne `workshop_codes` avec `SELECT ... FOR UPDATE`, revalide l’état, la période et la limite, réserve le numéro, crée `Participant` et `User` avec le rôle serveur `PARTICIPANT`, incrémente le compteur, écrit l’audit puis effectue un seul commit. Toute erreur annule les lignes et le compteur; le numéro de séquence peut rester consommé.

Les codes d’atelier sont générés côté serveur dans `/admin/workshop-codes`. Seule leur empreinte HMAC-SHA-256, calculée avec `WORKSHOP_CODE_SECRET`, indexée et unique, est stockée. Le code en clair n’est montré qu’une fois après création. Les administrateurs peuvent activer ou désactiver le code, définir sa période et sa limite, et consulter son compteur. Les actions sont auditées sans secret. Changer cette clé invalide les codes existants; sa rotation doit donc s’accompagner de leur remplacement contrôlé.

## Sécurité et exploitation

- Le mot de passe est validé entre 12 et 64 caractères et 72 octets UTF-8 maximum, puis haché par le mécanisme bcrypt existant.
- Les réponses et audits ne contiennent ni mot de passe, ni code d’atelier, ni prochaine valeur de séquence.
- Les formulaires utilisent le double jeton CSRF existant; les cookies de session restent `HttpOnly`, `Secure` selon la configuration et `SameSite=Strict`.
- La connexion est limitée après dix échecs sur cinq minutes par identifiant et adresse. L’inscription est limitée à 60 requêtes sur dix minutes par adresse. Ce limiteur est en mémoire du processus; un déploiement multi-réplicas doit placer un limiteur partagé au reverse proxy ou dans un stockage commun.
- Les erreurs de connexion restent génériques. Le code `MOS_NNN` est public et ne constitue pas un secret.
- L’administrateur peut consulter l’identifiant, désactiver/réactiver le compte et remplacer le mot de passe depuis `/participants`; l’ancien mot de passe n’est jamais accessible et chaque action est auditée.

## Migration 0004

`0004_participant_registration` :

1. verrouille les tables d’identité pendant le contrôle historique;
2. refuse les liens participant multiples, les paires `MOS_…` divergentes et les alias numériques tels que `MOS_001`/`MOS_0001`;
3. ajoute l’unicité de `users.participant_id`;
4. crée et positionne la séquence après le plus grand identifiant `MOS_NNN` trouvé dans les utilisateurs ou participants, sans renumérotation;
5. crée `workshop_codes`, ses contraintes et index.

Le downgrade est volontairement bloqué : supprimer le registre ou la séquence permettrait une réutilisation d’identité. Un retour arrière fiable exige l’arrêt des écritures et la restauration de la sauvegarde prise avant migration.

## Déploiement

1. Sauvegarder PostgreSQL et vérifier la restauration sur un environnement isolé.
2. Définir un `WORKSHOP_CODE_SECRET` aléatoire distinct d’au moins 32 caractères et arrêter les écritures applicatives pendant la migration, car le contrôle historique prend un verrou.
3. Exécuter `alembic upgrade head`.
4. Déployer l’application et vérifier `/health`, `/login`, `/participant/register` et `/admin/workshop-codes`.
5. Créer un code d’essai limité à une inscription, effectuer une inscription et vérifier la connexion avec le `MOS_NNN` obtenu.
6. Désactiver le code d’essai et vérifier l’audit.

Pour revenir en arrière, ne pas appeler `alembic downgrade`: arrêter les écritures, remettre la version applicative précédente et restaurer la sauvegarde pré-migration. Les identités créées après la sauvegarde devront être traitées explicitement; elles ne peuvent pas être supprimées silencieusement.

## Vérifications manuelles recommandées

- téléphone Android et navigateur mobile, réseau lent et double clic;
- navigation clavier, lecteur d’écran, contraste et copie de l’identifiant;
- code absent, invalide, futur, expiré, désactivé et à sa limite;
- tentative d’ajout de `role`, `is_superuser`, `username` ou `sequence_number` avec les outils navigateur;
- inspection des journaux afin de confirmer l’absence de mot de passe et de code en clair.

## Risques résiduels

- Le limiteur applicatif en mémoire n’est pas partagé entre plusieurs processus ou réplicas; Traefik ou un stockage distribué doit compléter le contrôle lors d’une montée en charge.
- Les dates d’atelier sont saisies et comparées dans l’heure serveur actuelle; l’interface devra expliciter le fuseau si des administrateurs opèrent depuis plusieurs zones.
- Le parcours administratif historique `/participants` conserve la saisie manuelle de ses identifiants pour compatibilité. Il reste strictement réservé au rôle `ADMIN`; seule l’auto-inscription publique garantit le format `MOS_NNN` et l’identité identique dans les deux tables.

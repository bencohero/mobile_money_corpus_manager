# G6 — Validation finale de release

## Résultats

| Contrôle | Résultat | Preuve / limite |
|---|---|---|
| Python | PASS — 159 pass, 1 skip, 8 warnings | Exécuté dans la stack Docker G5 isolée, 132,48 s |
| JavaScript | PASS — 10 pass | `node --test tests/*.test.cjs` |
| Playwright G5.1 | PASS documenté — 72 contrôles | Chromium réel, 320/360/390/412/1280/1440 ; replay complet non relancé faute de stack/browser cible déjà provisionnés |
| Responsive | PASS | 0 overflow, 0 erreur navigateur inattendue dans les artefacts G5.1 |
| Compose G5 | PASS | Résolution avec variables synthétiques ; réseau/volumes dédiés |
| Compose production | PRÉREQUIS | Échec sans `.env` ; attendu, aucun secret ne doit être créé dans le dépôt |
| Sécurité | PARTIELLEMENT REJOUÉ | compilation, shell et recherche de secrets passent ; `bandit`, `pip-audit`, `gitleaks` absents de l’hôte ; rapports G5 antérieurs disponibles |
| Garde Alembic | PASS | `assert_schema_current()` au startup ; migration uniquement via `scripts/migrate.sh` |
| Migration implicite | PASS | Aucun `alembic upgrade` dans les commandes startup validées ; aucun `create_all` au chemin startup |
| Restauration isolée | PASS documenté | Clone PostgreSQL/MinIO isolé restauré et vérifié lors de G5 |

## Warnings résiduels

Les 8 warnings Python sont des dépréciations connues : `crypt` via passlib, FastAPI `on_event`, Starlette/httpx et quatre usages de `datetime.utcnow()`. Ils ne sont pas des échecs de release mais doivent être traités dans une dette technique séparée.

Le microphone Playwright est simulé par Chromium (`--use-fake-device-for-media-stream`) : démarrage, arrêt et upload synthétique sont couverts ; la qualité acoustique, les périphériques physiques, les permissions OS et les variations matérielles ne le sont pas.

## Verdict de validation

Les validations applicatives sont suffisantes pour une revue de promotion conditionnelle. Le verdict global reste bloqué par les artefacts `.pyc` versionnés et par la sécurité complète non rejouée localement avec les scanners installés.

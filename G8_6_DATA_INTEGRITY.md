# G8.6 — Intégrité des données

## Constats

Les lectures PostgreSQL après la recette sans écriture métier donnent :

```text
users=21
participants=17
utterances=13
recordings=15
transcriptions=1
audit_logs=116
recording_submissions=15
recording_take_counters=15
rate_limit_buckets=1
```

Le bucket unique est la trace technique du test `workshop-language`, détaillée
dans [G8_6_PRECHECK.md](G8_6_PRECHECK.md). Les tables historiques et les tables
de corpus n'ont pas augmenté.

MinIO : 30 objets, 5 289 708 octets. L'audio historique 1 a répondu en lecture
complète/partielle et les contrôles de Range n'ont pas modifié l'objet.

## Nettoyage

Aucun nettoyage n'a été réalisé. Le bucket de rate limit est conservé car une
suppression immédiate serait destructive et la propriété de la ligne préexistante
ne peut pas être démontrée avec certitude. Il expirera selon `expires_at` si le
service reste actif.

Il n'y a eu aucune création d'objet MinIO pendant les tests exécutés. L'absence
d'objet orphelin supplémentaire est cohérente avec le nombre d'objets stable,
mais une preuve complète par manifeste avant/après de l'archive n'a pas été
recalculée dans cette phase.

## Traces d'audit

`audit_logs` est resté à 116. Le rate limiter ne produit pas d'audit métier ; sa
trace est la ligne `rate_limit_buckets` précisée ci-dessus.


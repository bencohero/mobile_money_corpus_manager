# G8.6 — Tests de sécurité

## Contrôles exécutés

- Trusted Host : hôte approuvé accepté ; hôte arbitraire refusé en 400.
- Contrôle d'accès : absence de session en 401 ; rôles insuffisants en 403.
- IDOR audio : accès d'un participant à l'audio d'un autre participant refusé.
- Sécurité des fichiers audio : audio autorisé en 200 ; Range valide en 206 ;
  Range impossible en 416.
- Requête malformée : endpoint de registration sans CSRF refusé en 403 ;
  tentative d'upload sans fichier refusée en 422. Aucune donnée n'a été créée.
- En-têtes : CSP, `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy` et HSTS observés sur les réponses.
- Surface réseau : le conteneur app n'a aucun port publié, aucun label Traefik
  et aucune attache au réseau frontend.

## Rate limiting

Le rate limiter persistant est bien actif sur la route publique de langue. Le
contrôle a laissé une trace contrôlée dans `rate_limit_buckets` : un seul
bucket `workshop-language`, compteur 1 et expiration à dix minutes. Cela prouve
la persistance, mais ne constitue pas un test de saturation ni un test de charge.

Aucun test agressif, aucune saturation et aucune série de soumissions métier
n'ont été déclenchés.

## Non exécuté

Les tests de session réelle, CSRF valide, permissions d'écriture,
transcription/vérification et export authentifié avec création de fichier sont
bloqués par le gel opérationnel et l'absence d'identités de recette dédiées
approuvées.


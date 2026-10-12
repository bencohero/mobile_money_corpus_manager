# F5A8 — décision finale

`RESTORE_VERIFIED`

La sauvegarde F5A7.2 a été restaurée avec succès dans un environnement PostgreSQL 16 + MinIO entièrement isolé. Les comptages, contraintes, relations, références audio, tailles d’objets et fichiers WAV sont cohérents.

Les ressources temporaires F5A8 ont été nettoyées après validation, de façon limitée et explicite : deux conteneurs F5A8, deux volumes anonymes créés par ces conteneurs et le réseau `f5a8-restore-net`. Aucun conteneur, volume ou réseau préexistant de production n’a été supprimé.

La conclusion ne signifie pas que l’archive est restaurable en production sans procédure de changement : toute restauration opérationnelle doit rester précédée d’une fenêtre autorisée, d’un arrêt des écritures et d’un contrôle indépendant.

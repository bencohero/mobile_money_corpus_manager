# G9.1 — Réconciliation des données

Comparer source et cible à partir des inventaires capturés avant restore, jamais
à partir d’un accès libre à la production après le gel.

Comparer la révision Alembic et les compteurs de users, participants, workshops,
workshop_codes, utterances, recordings, submissions, recording_take_counters,
transcriptions, transcription_history et audit_logs. Comparer un échantillon
déterministe d’identifiants, statuts, tailles, noms d’objets et SHA-256; ne pas
publier de contenu audio.

Comparer les inventaires MinIO JSON récursifs : chemins relatifs, nombre
d’objets, tailles, ETag lorsque pertinent et SHA-256. Exiger zéro objet manquant
et zéro objet orphelin.

scripts/reconcile.py --json doit retourner [] et code 0 sur l’application
isolée. Permission, timeout et indisponibilité restent distincts d’un objet
absent. Joindre au rapport inventaires, compteurs, révision Alembic, résultats
ready/health, sortie de réconciliation et empreintes.


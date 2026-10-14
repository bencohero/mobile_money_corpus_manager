#!/usr/bin/env bash
set -Eeuo pipefail

# Run once on the VPS. The operator supplies the historical password; it is
# sent only via stdin to the internal app container and never printed.
APP_CONTAINER="${APP_CONTAINER:-mobile_money_corpus_manager_g8_5_r-app}"
if [[ ! -t 0 ]]; then
  echo "Refus: saisie interactive masquée obligatoire." >&2
  exit 2
fi
read -r -s -p "Ancien mot de passe benco: " OLD_PASSWORD
printf '\n' >&2
[[ -n "$OLD_PASSWORD" ]] || { echo "Refus: mot de passe vide." >&2; exit 2; }

printf '%s\n' "$OLD_PASSWORD" | docker exec -i "$APP_CONTAINER" sh -lc '
set -Eeuo pipefail
IFS= read -r PASSWORD
d=$(mktemp -d); chmod 700 "$d"
trap '\''unset PASSWORD; rm -rf "$d"'\'' EXIT
curl -fsS -D "$d/get.h" -o "$d/get.b" \
  -H "Host: corpus-moore.bencoherolab.com" http://127.0.0.1:8000/login
csrf=$(sed -n '\''s/.*name="csrf_token" value="\([^"]*\)".*/\1/p'\'' "$d/get.b")
cookie=$(sed -n '\''s/^set-cookie: csrf_token=\([^;]*\).*/\1/Ip'\'' "$d/get.h" | head -n 1)
test -n "$csrf"; test -n "$cookie"
code=$(curl -sS -o /dev/null -w "%{http_code}" -X POST \
  -H "Host: corpus-moore.bencoherolab.com" -H "Cookie: csrf_token=$cookie" \
  --data-urlencode "username=benco" --data-urlencode "password=$PASSWORD" \
  --data-urlencode "csrf_token=$csrf" http://127.0.0.1:8000/login)
test "$code" = 401
unset PASSWORD csrf cookie
echo "old_login=401"
'
unset OLD_PASSWORD

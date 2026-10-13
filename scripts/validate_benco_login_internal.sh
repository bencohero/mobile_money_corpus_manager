#!/usr/bin/env bash
set -Eeuo pipefail

# Run on the VPS. Never prints the password, cookies, or CSRF values.
APP_CONTAINER="${APP_CONTAINER:-mobile_money_corpus_manager_g8_5_r-app}"
APP_URL="http://127.0.0.1:8000"
APP_HOST="${APP_HOST:-corpus-moore.bencoherolab.com}"

if [[ ! -t 0 ]]; then
  echo "Refus: saisie interactive masquée obligatoire." >&2
  exit 2
fi
read -r -s -p "Nouveau mot de passe benco: " NEW_PASSWORD
printf '\n' >&2
[[ -n "$NEW_PASSWORD" ]] || { echo "Refus: mot de passe vide." >&2; exit 2; }

# Bash owns the masked prompt; the inner /bin/sh only uses portable read -r.
printf '%s\n' "$NEW_PASSWORD" | docker exec -i "$APP_CONTAINER" sh -lc '
set -Eeuo pipefail
IFS= read -r PASSWORD
APP_URL="http://127.0.0.1:8000"
APP_HOST="corpus-moore.bencoherolab.com"
TMP_DIR=$(mktemp -d); chmod 700 "$TMP_DIR"
trap '\''unset PASSWORD; rm -rf "$TMP_DIR"'\'' EXIT
GET_HEADERS="$TMP_DIR/get.headers"; GET_BODY="$TMP_DIR/get.body"
POST_HEADERS="$TMP_DIR/post.headers"; POST_BODY="$TMP_DIR/post.body"

curl -fsS -D "$GET_HEADERS" -o "$GET_BODY" -H "Host: $APP_HOST" "$APP_URL/login"
CSRF_FORM=$(sed -n '\''s/.*name="csrf_token" value="\([^"]*\)".*/\1/p'\'' "$GET_BODY")
CSRF_COOKIE=$(sed -n '\''s/^set-cookie: csrf_token=\([^;]*\).*/\1/Ip'\'' "$GET_HEADERS" | head -n 1)
test -n "$CSRF_FORM"; test -n "$CSRF_COOKIE"

LOGIN_CODE=$(curl -sS -D "$POST_HEADERS" -o "$POST_BODY" -w "%{http_code}" -X POST \
  -H "Host: $APP_HOST" -H "Cookie: csrf_token=$CSRF_COOKIE" \
  --data-urlencode "username=benco" --data-urlencode "password=$PASSWORD" \
  --data-urlencode "csrf_token=$CSRF_FORM" "$APP_URL/login")
SESSION_COOKIE=$(sed -n '\''s/^set-cookie: session=\([^;]*\).*/\1/Ip'\'' "$POST_HEADERS" | head -n 1)
test "$LOGIN_CODE" = 303; test -n "$SESSION_COOKIE"

ADMIN_CODE=$(curl -sS -o /dev/null -w "%{http_code}" -H "Host: $APP_HOST" \
  -H "Cookie: csrf_token=$CSRF_COOKIE; session=$SESSION_COOKIE" "$APP_URL/users")
test "$ADMIN_CODE" = 200
LOGOUT_CODE=$(curl -sS -o /dev/null -w "%{http_code}" -X POST -H "Host: $APP_HOST" \
  -H "Cookie: csrf_token=$CSRF_COOKIE; session=$SESSION_COOKIE" \
  --data-urlencode "csrf_token=$CSRF_FORM" "$APP_URL/logout")
test "$LOGOUT_CODE" = 303
unset PASSWORD CSRF_FORM CSRF_COOKIE SESSION_COOKIE
echo "login=303 admin-users=200 logout=303"
'
unset NEW_PASSWORD

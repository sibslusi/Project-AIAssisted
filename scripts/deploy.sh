#!/usr/bin/env bash
# Löst den Render Deploy Hook für genau das geprüfte Image aus.
# Erwartet RENDER_DEPLOY_HOOK_URL (Secret, enthält schon ?key=...) und IMAGE.
set -euo pipefail

: "${RENDER_DEPLOY_HOOK_URL:?RENDER_DEPLOY_HOOK_URL muss gesetzt sein}"
: "${IMAGE:?IMAGE muss gesetzt sein}"

encoded_image="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$IMAGE")"

# Die Hook-URL wird nie ausgegeben; curl -sS zeigt bei Fehlern nur den Status.
curl -fsS -X POST --output /dev/null "${RENDER_DEPLOY_HOOK_URL}&imgURL=${encoded_image}"
echo "Deploy für ${IMAGE} bei Render ausgelöst"

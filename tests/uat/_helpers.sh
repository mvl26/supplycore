#!/usr/bin/env bash
# Helpers cho UAT REST API testing
export BASE="http://localhost:8000"
export HOSTH="Host: supplycore"
export AUTHH="Authorization: token a2e2db8626df901:b3a5b46d7e9129e"
export CTH="Content-Type: application/json"

# Encode doctype name with %20 for URL
enc() { python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$1"; }

# api_get DOCTYPE NAME → returns body
api_get_doc() {
  curl -sS -H "$HOSTH" -H "$AUTHH" "$BASE/api/resource/$(enc "$1")/$(enc "$2")"
}

# api_list DOCTYPE filters_json fields_json
api_list() {
  local f="${2:-{}}"; local fl="${3:-[\"name\"]}"
  curl -sS -G -H "$HOSTH" -H "$AUTHH" \
    --data-urlencode "filters=$f" --data-urlencode "fields=$fl" \
    --data-urlencode "limit_page_length=20" \
    "$BASE/api/resource/$(enc "$1")"
}

# api_post DOCTYPE json
api_post_doc() {
  curl -sS -H "$HOSTH" -H "$AUTHH" -H "$CTH" -X POST \
    -d "$2" "$BASE/api/resource/$(enc "$1")"
}

# api_method full.path json
api_method() {
  curl -sS -H "$HOSTH" -H "$AUTHH" -H "$CTH" -X POST \
    -d "$2" "$BASE/api/method/$1"
}

# api_submit DOCTYPE NAME — uses frappe.client.submit
api_submit() {
  curl -sS -H "$HOSTH" -H "$AUTHH" -H "$CTH" -X POST \
    --data-urlencode "doctype=$1" --data-urlencode "name=$2" \
    "$BASE/api/method/frappe.client.submit"
}

# log_uat MODULE STEP STATUS DETAIL
log_uat() {
  local mod="$1" step="$2" status="$3" detail="$4"
  echo "| $step | $status | $detail |" >> "/tmp/uat_${mod}.log"
}

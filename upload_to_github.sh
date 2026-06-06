#!/bin/bash
# Uploads files to a GitHub repo via the Contents API.
# Token must be in $GITHUB_TOKEN env var. Token is never written to disk in the repo.

set -euo pipefail
: "${GITHUB_TOKEN:?GITHUB_TOKEN env var is required}"
: "${REPO_OWNER:?REPO_OWNER env var is required}"
: "${REPO_NAME:?REPO_NAME env var is required}"
: "${SRC_DIR:?SRC_DIR env var is required}"

BRANCH="main"
API="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents"

upload_file() {
    local relpath="$1"
    local fullpath="${SRC_DIR}/${relpath}"
    if [[ ! -f "$fullpath" ]]; then
        echo "SKIP (not a file): $relpath"
        return
    fi
    # base64 encode (no line wraps)
    local b64
    b64=$(base64 -w 0 "$fullpath")
    local payload
    payload=$(python3 -c "import json,sys; print(json.dumps({'message':'upload '"'"'$relpath'"'"'','branch':'$BRANCH','content':sys.stdin.read()}))" <<< "$b64")
    # Check if file already exists to get its sha (required for update)
    local sha=""
    local existing
    existing=$(curl -s -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
        "${API}/$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe='/'))" "$relpath")?ref=$BRANCH" || true)
    sha=$(echo "$existing" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('sha',''))" 2>/dev/null || echo "")
    if [[ -n "$sha" ]]; then
        payload=$(python3 -c "import json,sys; print(json.dumps({'message':'update '"'"'$relpath'"'"'','branch':'$BRANCH','content':sys.stdin.read(),'sha':'$sha'}))" <<< "$b64")
    fi
    local resp
    resp=$(curl -s -X PUT -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
        -d "$payload" "${API}/$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe='/'))" "$relpath")")
    local path html_url commit_msg
    path=$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('content',{}).get('path',''))" 2>/dev/null || echo "")
    html_url=$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('content',{}).get('html_url',''))" 2>/dev/null || echo "")
    commit_msg=$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('commit',{}).get('message',''))" 2>/dev/null || echo "")
    if [[ -n "$path" ]]; then
        echo "OK  $relpath -> $html_url"
    else
        echo "ERR $relpath"
        echo "$resp" | head -3
        return 1
    fi
}

export -f upload_file
export GITHUB_TOKEN REPO_OWNER REPO_NAME SRC_DIR BRANCH API

# Collect all files
mapfile -t files < <(cd "$SRC_DIR" && find . -type f | sort)
echo "Files to upload: ${#files[@]}"
for f in "${files[@]}"; do
    rel="${f#./}"
    upload_file "$rel"
done
echo "Done."

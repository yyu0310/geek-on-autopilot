#!/usr/bin/env bash
# site_lock_check.sh: check that an invite-only site gives nothing to an anonymous visitor.
#
# Sends about 40 unauthenticated requests to your host and its subdomains (path variants,
# HTTP methods, forged headers, common branch subdomains, Cloudflare Access endpoints)
# and judges each response by its status code, its size, and your marker string.
#
# Usage:
#   bash site_lock_check.sh <host> '<marker>' [deploy-url-file]
#   bash site_lock_check.sh --selftest
#   host              bare host name, for example example.pages.dev
#   marker            a string only the real page contains, as an egrep (ERE) pattern. Several
#                     alternatives with | between them. Escape special characters, for example
#                     'report \(USD\)' or 'C\+\+'. An invalid pattern is refused with exit 2.
#   deploy-url-file   optional: one full URL per line (the per-deployment hash URLs)
#   EXTRA_PATHS       optional environment variable for multi-page sites, e.g. EXTRA_PATHS='/page2.html /b'
#
# Verdict per request (a request is counted as FAIL unless it matches a PASS rule):
#   FAIL  the body contains the marker
#   FAIL  the body is 100 KB or larger (except under /cdn-cgi/access/)
#   FAIL  any 2xx status, except the Cloudflare paths listed below (shown as PASS exempt_200)
#   FAIL  no response (status 000) from the host itself or from a URL in the deploy-url-file
#   FAIL  any status not listed under PASS, such as 401, 405, or 5xx (look at it by hand)
#   PASS  status 301, 302, 303, 307, 308, 400, 403, or 404
#   PASS  no response (000) from one of the built-in guessed-subdomain probes only (a subdomain
#         that does not exist is fine). A deployment URL you listed must answer.
# Exempt 2xx paths (documented Cloudflare endpoints, not your page): /cdn-cgi/trace and
# /cdn-cgi/access/*. A 200 there is marked exempt in the output; the marker and size rules still apply.
# If no request to the host itself got any response, the run ends with exit 6, so a mistyped
# host or a dead network can never look like a pass.
#
# Safety boundary (kept on purpose):
#   - It only requests the given host and its subdomains. Any other URL is refused.
#   - It never triggers a one-time-PIN email, never guesses a PIN, never submits a login.
#   - It never follows redirects (--max-redirs 0), so a login redirect is seen, not followed.
#   - Run it only against a site you own or are authorized to test.
#
# Exit codes: 0 all passed, 2 bad arguments (including an invalid marker), 3 deploy-url-file
#             not found, 4 at least one request failed, 5 curl is missing,
#             6 no request to the host got a response.
set +e

CURL="${CURL_BIN:-curl}"
UA='site-lock-check/1.0'
PASS=0
FAIL=0
REACHED=0
ACCEPT_000=0   # 1 only while the built-in guessed-subdomain probes run

usage() {
  echo "usage: site_lock_check.sh <host> '<marker>' [deploy-url-file]" >&2
  echo "       site_lock_check.sh --selftest" >&2
}

# A bare host such as example.pages.dev: letters, digits, dots, hyphens, at least one dot.
valid_host() {
  case "$1" in
    ''|*[!A-Za-z0-9.-]*|.*|*.|-*|*..*) return 1 ;;
    *.*) return 0 ;;
    *) return 1 ;;
  esac
}

# Is the URL on $HOST or one of its subdomains, over http or https?
in_scope() {
  local u="$1" rest h
  case "$u" in
    https://*) rest="${u#https://}" ;;
    http://*) rest="${u#http://}" ;;
    *) return 1 ;;
  esac
  h="${rest%%[/?#]*}"
  case "$h" in *@*|*:*) return 1 ;; esac
  [ "$h" = "$HOST" ] && return 0
  case "$h" in *."$HOST") return 0 ;; esac
  return 1
}

url_host() { local r="${1#*://}"; echo "${r%%[/?#]*}"; }

url_path() { local r="${1#*://}"; case "$r" in */*) echo "/${r#*/}" ;; *) echo "/" ;; esac; }

# Documented Cloudflare endpoints where a 200 is normal.
exempt_path() {
  case "$(url_path "$1")" in
    /cdn-cgi/trace|/cdn-cgi/access|/cdn-cgi/access/*) return 0 ;;
  esac
  return 1
}

check() {
  local url="$1"; shift
  local body; body=$(mktemp)
  local out code n gs r
  out=$("$CURL" -sS -A "$UA" --max-redirs 0 --http1.1 --max-time 20 -o "$body" \
    -w 'http_code=%{http_code} size=%{size_download}' "$@" "$url" 2>&1)
  code=$(printf '%s' "$out" | sed -n 's/.*http_code=\([0-9][0-9][0-9]\).*/\1/p' | tail -1)
  [ -z "$code" ] && code=000
  n=$(wc -c < "$body" | tr -d ' ')
  LC_ALL=C grep -q -E -- "$MARKER" "$body"; gs=$?   # byte-wise: a body with invalid UTF-8 must not break matching
  local on_host=0
  [ "$(url_host "$url")" = "$HOST" ] && on_host=1
  if [ "$on_host" = 1 ] && [ "$code" != 000 ]; then REACHED=$((REACHED+1)); fi
  if [ "$gs" -eq 0 ]; then r="FAIL marker_present"
  elif [ "$gs" -ge 2 ]; then r="FAIL marker_check_error"
  elif [ "${n:-0}" -ge 100000 ] && ! echo "$url" | grep -q '/cdn-cgi/access/'; then r="FAIL body_large"
  elif [ "$code" = 000 ]; then
    if [ "$on_host" = 0 ] && [ "$ACCEPT_000" = 1 ]; then r="PASS no_response_accepted"; else r="FAIL no_response"; fi
  else
    case "$code" in
      2??) if exempt_path "$url"; then r="PASS exempt_$code"; else r="FAIL status_$code"; fi ;;
      301|302|303|307|308|400|403|404) r="PASS" ;;
      *) r="FAIL unexpected_status_$code" ;;
    esac
  fi
  case "$r" in PASS*) PASS=$((PASS+1)) ;; *) FAIL=$((FAIL+1)) ;; esac
  printf '%-26s %s | %s | %s\n' "$r" "$out" "$url" "$*"
  rm -f "$body"
}

run_all() {
  local p name
  for p in '/' '/index.html' '/Index.html' '/INDEX.HTML' '/index.html/' '//' '/%2e/index.html' '/index.html%3f' '/?x=1' '/this-path-should-not-exist'; do
    check "https://$HOST$p"
  done
  check "http://$HOST/"
  ACCEPT_000=1
  check "https://a.b.$HOST/"
  for name in main www preview master dev staging production prod release test testing ci; do
    check "https://${name}.$HOST/"
  done
  ACCEPT_000=0
  for p in '' login get-identity logout cli authorized certs; do
    check "https://$HOST/cdn-cgi/access/$p"
  done
  check "https://$HOST/cdn-cgi/trace"
  check "https://$HOST/" -I
  check "https://$HOST/" -X POST
  check "https://$HOST/" -X PUT
  check "https://$HOST/" -X OPTIONS
  check "https://$HOST/" -H 'Range: bytes=0-200'
  check "https://$HOST/" -H 'Cf-Access-Authenticated-User-Email: not-on-list@example.com' -H 'Cf-Access-Jwt-Assertion: not-a-jwt' -H 'X-Forwarded-For: 127.0.0.1' -H "X-Forwarded-Host: $HOST"
  check "https://$HOST/" -H 'Host: example.com'
  # other page paths (multi-page sites, for example /page2.html)
  set -f   # no glob expansion of EXTRA_PATHS
  for p in $EXTRA_PATHS; do check "https://$HOST$p"; done
  set +f
  # per-deployment hash URLs: the Deployment column of `wrangler pages deployment list --project-name X --json`
  if [ -n "$HASHFILE" ]; then
    local u
    while read -r u; do
      [ -z "$u" ] && continue
      if in_scope "$u"; then check "$u"; else echo "SKIP   out of scope, not requested: $u"; fi
    done < "$HASHFILE"
  fi
}

run_main() {
  HOST="$1"; MARKER="$2"; HASHFILE="$3"
  if [ -z "$HOST" ] || [ -z "$MARKER" ]; then usage; return 2; fi
  if ! valid_host "$HOST"; then echo "ERROR: host must be a bare name such as example.pages.dev, got: $HOST" >&2; return 2; fi
  local p
  set -f
  for p in $EXTRA_PATHS; do
    case "$p" in /*) ;; *) set +f; echo "ERROR: EXTRA_PATHS entries must start with /, got: $p" >&2; return 2 ;; esac
    case "$p" in *@*) set +f; echo "ERROR: EXTRA_PATHS entries must not contain @, got: $p" >&2; return 2 ;; esac
  done
  set +f
  echo x | LC_ALL=C grep -q -E -- "$MARKER" 2>/dev/null
  if [ $? -eq 2 ]; then echo "ERROR: marker is not a valid egrep (ERE) pattern: $MARKER" >&2; return 2; fi
  if [ -n "$HASHFILE" ] && [ ! -f "$HASHFILE" ]; then echo "ERROR: deploy-url-file not found: $HASHFILE" >&2; return 3; fi
  if ! command -v "$CURL" >/dev/null 2>&1; then echo "ERROR: curl not found (set CURL_BIN or install curl)" >&2; return 5; fi
  run_all
  echo "SUMMARY pass=$PASS fail=$FAIL"
  if [ "$REACHED" -eq 0 ]; then
    echo "ERROR: no probe reached the host (check the host name and your network)" >&2
    return 6
  fi
  [ "$FAIL" -eq 0 ] && return 0
  return 4
}

# ---------- selftest: a fake curl, no network ----------

selftest() {
  local self tmp ok=0 total=0
  self="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/site_lock_selftest.XXXXXX")
  trap 'rm -rf "$tmp"' EXIT

  t() { total=$((total+1)); if [ "$1" = "0" ]; then ok=$((ok+1)); echo "[PASS] $2"; else echo "[FAIL] $2"; fi; }

  # fake curl: logs its arguments, writes a body chosen by FAKE_MODE, prints the -w text
  cat > "$tmp/fakecurl" <<'FAKE'
#!/usr/bin/env bash
echo "$*" >> "$FAKE_LOG"
out=""; url=""
while [ $# -gt 0 ]; do
  case "$1" in
    -o) out="$2"; shift 2 ;;
    -w|-A|--max-redirs|--max-time|-X|-H) shift 2 ;;
    -sS|--http1.1|-I) shift ;;
    *) url="$1"; shift ;;
  esac
done
: > "$out"
size=0
case "$FAKE_MODE:$url" in
  leak_marker:"https://$FAKE_HOST/index.html") echo "page text SECRET-MARKER-123 here" > "$out" ;;
  cjk:"https://$FAKE_HOST/index.html") printf '\xff\xfe page \xe6\xb8\xac\xe8\xa9\xa6\xe6\xa8\x99\xe8\xa8\x98 \x80\n' > "$out" ;;
  leak_large:"https://$FAKE_HOST/Index.html") head -c 150000 /dev/zero | tr '\0' 'a' > "$out" ;;
  access_large:"https://$FAKE_HOST/cdn-cgi/access/certs") head -c 150000 /dev/zero | tr '\0' 'a' > "$out" ;;
esac
size=$(wc -c < "$out" | tr -d ' ')
code=302
case "$FAKE_MODE" in
  unreachable) code=000; echo "curl: (6) Could not resolve host" >&2 ;;
  public200) code=200; echo "welcome to the public page" > "$out"; size=$(wc -c < "$out" | tr -d ' ') ;;
  subdown) case "$url" in *"//$FAKE_HOST/"*) ;; *) code=000 ;; esac ;;
  access200) case "$url" in */cdn-cgi/access/certs|*/cdn-cgi/trace) code=200 ;; esac ;;
  e500) [ "$url" = "https://$FAKE_HOST/index.html" ] && code=500 ;;
esac
printf 'http_code=%s size=%s' "$code" "$size"
FAKE
  chmod +x "$tmp/fakecurl"

  export FAKE_LOG="$tmp/calls.log" FAKE_HOST="demo.example.pages.dev"
  local H="demo.example.pages.dev" rc out

  run() { : > "$FAKE_LOG"; out=$(CURL_BIN="$tmp/fakecurl" bash "$self" "$@" 2>&1); rc=$?; }

  # argument errors
  : > "$FAKE_LOG"
  out=$(CURL_BIN="$tmp/fakecurl" bash "$self" 2>&1); rc=$?
  [ "$rc" = 2 ] && echo "$out" | grep -q "usage:"; t $? "no arguments -> usage text, exit 2"
  run "$H"; [ "$rc" = 2 ]; t $? "missing marker -> exit 2"
  local bad=0 h
  for h in 'https://demo.example.pages.dev' 'demo.example.pages.dev/path' '*.example.pages.dev' 'nodot' 'a b.example.pages.dev' 'demo.example.pages.dev:8080' '.example.pages.dev' 'a..b.dev' 'user@demo.example.pages.dev'; do
    run "$h" X
    { [ "$rc" = 2 ] && [ ! -s "$FAKE_LOG" ]; } || { bad=1; echo "  not rejected: $h"; }
  done
  t $bad "bad host forms are rejected with exit 2 before any request"

  # clean site: every request passes
  FAKE_MODE=clean run "$H" 'SECRET-MARKER-123'
  [ "$rc" = 0 ] && echo "$out" | grep -q "SUMMARY pass=39 fail=0"; t $? "clean site -> exit 0 and SUMMARY pass=39 fail=0"

  # marker leak
  FAKE_MODE=leak_marker run "$H" 'SECRET-MARKER-123'
  [ "$rc" = 4 ] && echo "$out" | grep -q "FAIL marker_present" && echo "$out" | grep -q "fail=1"; t $? "marker in a body -> FAIL marker_present, exit 4"
  FAKE_MODE=leak_marker run "$H" 'nothing-here|SECRET-MARKER-123'
  [ "$rc" = 4 ]; t $? "several markers separated by | are all searched"

  # large body
  FAKE_MODE=leak_large run "$H" 'SECRET-MARKER-123'
  [ "$rc" = 4 ] && echo "$out" | grep -q "FAIL body_large"; t $? "body of 100 KB or more -> FAIL body_large, exit 4"
  FAKE_MODE=access_large run "$H" 'SECRET-MARKER-123'
  [ "$rc" = 0 ]; t $? "large body under /cdn-cgi/access/ is exempt"

  # safety boundary, read off the log of a full run
  FAKE_MODE=clean run "$H" 'SECRET-MARKER-123'
  local calls; calls=$(wc -l < "$FAKE_LOG" | tr -d ' ')
  [ "$calls" = 39 ]; t $? "a full run makes 39 requests (got $calls)"
  ! grep -qv -e '--max-redirs 0' "$FAKE_LOG"; t $? "every request sends --max-redirs 0 (redirects are never followed)"
  ! grep -qE -e '(^| )(-L|--location)( |$)' "$FAKE_LOG"; t $? "no request uses -L or --location"
  local scope_bad=0 u
  while read -r line; do
    u="${line##* }"
    HOST="$H" in_scope "$u" || { scope_bad=1; echo "  out of scope: $u"; }
  done < "$FAKE_LOG"
  t $scope_bad "every requested URL is on the host or its subdomains"
  local post_bad=0
  while read -r line; do
    case "$line" in *"-X POST"*|*"-X PUT"*) [ "${line##* }" = "https://$H/" ] || post_bad=1 ;; esac
  done < "$FAKE_LOG"
  t $post_bad "POST and PUT only go to the site root, never to a login endpoint"

  # EXTRA_PATHS
  EXTRA_PATHS='/page2.html /b' FAKE_MODE=clean run "$H" X
  grep -q "https://$H/page2.html" "$FAKE_LOG" && echo "$out" | grep -q "pass=41"; t $? "EXTRA_PATHS adds one request per path"
  EXTRA_PATHS='@evil.example.org/' FAKE_MODE=clean run "$H" X
  [ "$rc" = 2 ] && [ ! -s "$FAKE_LOG" ]; t $? "EXTRA_PATHS entry that could change the host is refused before any request"
  EXTRA_PATHS='noslash' FAKE_MODE=clean run "$H" X
  [ "$rc" = 2 ] && [ ! -s "$FAKE_LOG" ]; t $? "EXTRA_PATHS entry without a leading / is refused"

  : > "$tmp/Afile"
  : > "$FAKE_LOG"
  (cd "$tmp" && EXTRA_PATHS='/A*' FAKE_LOG="$FAKE_LOG" FAKE_MODE=clean CURL_BIN="$tmp/fakecurl" bash "$self" "$H" X > /dev/null 2>&1)
  grep -q "https://$H/A\*" "$FAKE_LOG" && ! grep -q "https://$H/Afile" "$FAKE_LOG"; t $? "EXTRA_PATHS is not glob-expanded by the shell"

  # invalid marker patterns are refused before any request (an invalid pattern must never look like a pass)
  local badm=0 m
  for m in 'C++' 'report (USD' 'a|' '[abc' '*x'; do
    FAKE_MODE=public200 run "$H" "$m"
    { [ "$rc" = 2 ] && [ ! -s "$FAKE_LOG" ] && echo "$out" | grep -q "not a valid egrep"; } || { badm=1; echo "  not refused: $m"; }
  done
  t $badm "invalid ERE markers (C++, unbalanced paren, empty alternative, ...) -> exit 2 before any request"
  FAKE_MODE=leak_marker run "$H" 'SECRET-MARKER-12[0-9]'
  [ "$rc" = 4 ]; t $? "a valid regex marker with a bracket class is matched"

  # status codes decide, not only the marker
  FAKE_MODE=public200 run "$H" 'a-marker-that-is-not-on-the-page'
  [ "$rc" = 4 ] && echo "$out" | grep -q "FAIL status_200" && ! echo "$out" | grep -q "fail=0"; t $? "public 200 page with a wrong marker -> FAIL status_200, exit 4"
  FAKE_MODE=access200 run "$H" 'SECRET-MARKER-123'
  [ "$rc" = 0 ] && echo "$out" | grep -q "PASS exempt_200" && [ "$(echo "$out" | grep -c 'PASS exempt_200')" = 2 ]; t $? "200 on /cdn-cgi/trace and /cdn-cgi/access/certs is allowed and marked exempt (2 lines)"
  FAKE_MODE=e500 run "$H" 'SECRET-MARKER-123'
  [ "$rc" = 4 ] && echo "$out" | grep -q "FAIL unexpected_status_500"; t $? "a status outside the PASS list (500) -> FAIL, exit 4"
  FAKE_MODE=unreachable run nope.example.invalid 'SECRET-MARKER-123'
  [ "$rc" = 6 ] && echo "$out" | grep -q "no probe reached the host" && ! echo "$out" | grep -q "fail=0"; t $? "host unreachable (all 000) -> exit 6, no fail=0"
  FAKE_MODE=subdown run "$H" 'SECRET-MARKER-123'
  [ "$rc" = 0 ] && echo "$out" | grep -q "PASS no_response_accepted" && echo "$out" | grep -q "fail=0"; t $? "000 on subdomain probes is accepted while the host itself answers"

  # a deployment URL from the file that does not answer is a failure, unlike the guessed subdomains
  printf 'https://abc123.%s\n' "$H" > "$tmp/urls2.txt"
  FAKE_MODE=subdown run "$H" 'SECRET-MARKER-123' "$tmp/urls2.txt"
  [ "$rc" = 4 ] && echo "$out" | grep -q "FAIL no_response.*abc123" && echo "$out" | grep -q "PASS no_response_accepted"; t $? "000 from a deploy-url-file URL -> FAIL no_response, guessed subdomains still accepted"

  # byte-wise matching: invalid UTF-8 in the body, CJK marker under a UTF-8 locale
  FAKE_MODE=cjk LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 run "$H" '測試標記'
  [ "$rc" = 4 ] && echo "$out" | grep -q "FAIL marker_present"; t $? "CJK marker is found in a body that contains invalid UTF-8 bytes"
  FAKE_MODE=cjk LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 run "$H" '不在頁面的字'
  echo "$out" | grep -q "FAIL marker_present"; [ $? -ne 0 ]; t $? "a CJK marker that is not on the page is not reported as present"

  # deploy URL file
  printf 'https://abc123.%s\n\nhttps://evil.example.org/\nhttps://%s.evil.example.org/\n' "$H" "$H" > "$tmp/urls.txt"
  FAKE_MODE=clean run "$H" X "$tmp/urls.txt"
  grep -q "https://abc123.$H" "$FAKE_LOG" && ! grep -q "evil.example.org" "$FAKE_LOG" && echo "$out" | grep -q "SKIP" && [ "$rc" = 0 ]
  t $? "deploy URL file: in-scope hash URL requested, out-of-scope URLs skipped and never requested"
  run "$H" X "$tmp/missing.txt"; [ "$rc" = 3 ]; t $? "missing deploy-url-file -> exit 3"

  # curl missing
  out=$(CURL_BIN="$tmp/no-such-curl" bash "$self" "$H" X 2>&1); rc=$?
  [ "$rc" = 5 ]; t $? "curl missing -> exit 5"

  echo
  echo "selftest result: $ok/$total passed"
  [ "$ok" = "$total" ]
}

if [ "$1" = "--selftest" ]; then
  selftest
  exit $?
fi
run_main "$1" "$2" "$3"
exit $?

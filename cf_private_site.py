#!/usr/bin/env python3
"""cf_private_site.py: manage the Cloudflare Access allowlist in front of a Pages site.

Used by the /private-site command. Standard library only; the API token is read from
a file you point to, and its value is never printed.

Usage (run with python3 -I so stray PYTHON* variables and local modules are ignored):
  python3 -I cf_private_site.py <command> --host <name>.pages.dev [email ...]

Commands:
  check     read-only: verify the token, list login methods, list the existing Access app
  emails    list the current allowlist
  apply     create the One-time PIN login method (only if missing) and the Access app
            (covers the host and *.host) with an Allow policy for the emails; if the app
            already exists, update its allowlist. This REPLACES the whole list, so always
            pass every email.
  harden    session 7 days by default (--session 168h), Binding cookie on, SameSite Lax,
            HttpOnly on

Credentials (required, no default path): set the environment variable CF_ENV_FILE to a
file you created yourself, outside any repository and out of reach of AI tools. It must
contain two lines, CLOUDFLARE_API_TOKEN=... and CLOUDFLARE_ACCOUNT_ID=... (a leading
"export " is accepted). The token needs Zero Trust edit permissions (Access: Apps and
Policies Edit, plus Edit on Organizations, Identity Providers, and Groups so that apply can
create One-time PIN when it is missing). Without CF_ENV_FILE the script prints a clear
error and exits 5.

Exit codes:
  0  success
  2  bad arguments, or an API or network failure
  4  hard gate failed (for example harden found no policy and stopped to protect the allowlist)
  5  credentials missing or unusable

--selftest runs the built-in tests with a fake Cloudflare API. No network, no real token.
"""
import argparse
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"
HOST_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")
EMAIL_RE = re.compile(r"^[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+$")


class ToolError(Exception):
    """An error that ends the run with a specific exit code."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


# ---------- pure helpers ----------

def load_env(path):
    env = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get_credentials(environ):
    """Return (token, account id). Raises ToolError(5) with a clear message when unusable.
    The token value is never included in a message."""
    path = environ.get("CF_ENV_FILE")
    if not path:
        raise ToolError(5, "CF_ENV_FILE is not set. Create a file outside any repository with the lines "
                           "CLOUDFLARE_API_TOKEN=... and CLOUDFLARE_ACCOUNT_ID=... , then run: "
                           "CF_ENV_FILE=/path/to/that/file python3 -I cf_private_site.py <command> --host <name>.pages.dev")
    try:
        env = load_env(path)
    except OSError as e:
        raise ToolError(5, f"CF_ENV_FILE points at a file that cannot be read ({e.strerror}): {path}")
    missing = [k for k in ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID") if not env.get(k)]
    if missing:
        raise ToolError(5, f"CF_ENV_FILE is missing: {', '.join(missing)}")
    return env["CLOUDFLARE_API_TOKEN"], env["CLOUDFLARE_ACCOUNT_ID"]


def valid_host(host):
    """Lowercased host name, or None. Rejects schemes, paths, wildcards, and ports."""
    h = (host or "").strip().lower()
    return h if HOST_RE.match(h) else None


def parse_emails(raw):
    """Split on whitespace, commas, and semicolons; lowercase; drop duplicates (first wins).
    Returns (emails, invalid)."""
    seen, emails, invalid = set(), [], []
    for item in re.split(r"[\s,;]+", " ".join(raw)):
        item = item.strip().lower()
        if not item:
            continue
        if not EMAIL_RE.match(item):
            invalid.append(item)
        elif item not in seen:
            seen.add(item)
            emails.append(item)
    return emails, invalid


def policy_body(emails):
    return {"name": "invited emails", "decision": "allow",
            "include": [{"email": {"email": e}} for e in emails]}


def emails_from_policy(policy):
    return [i["email"]["email"] for i in policy.get("include") or []
            if isinstance(i, dict) and isinstance(i.get("email"), dict) and "email" in i["email"]]


# ---------- Cloudflare API ----------

class Client:
    def __init__(self, token, account, opener=None):
        self.token = token
        self.account = account
        self.opener = opener or urllib.request.urlopen

    def call(self, method, path, body=None):
        req = urllib.request.Request(
            f"{API}/accounts/{self.account}{path}", method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json",
                     "User-Agent": "private-site-setup"})
        try:
            with self.opener(req, timeout=30) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            try:
                data = json.loads(e.read() or b"{}")
            except ValueError:
                data = {}
        except (urllib.error.URLError, OSError) as e:
            raise ToolError(2, f"network error on {method} {path}: {e}")
        print(f"  {method} {path} -> success={data.get('success')} errors={data.get('errors')}")
        return data

    def find_app(self, host):
        """The Access app that protects exactly this host, matched by domain or destination only.
        A name match is deliberately not used: another site's app can share the name."""
        for a in self.call("GET", "/access/apps").get("result") or []:
            doms = [a.get("domain")] + [d.get("uri") for d in a.get("destinations") or []]
            if host in doms:
                return a
        return None


# ---------- commands ----------

def run_command(client, cmd, host, emails, session):
    name = host.split(".")[0]

    print("token verification")
    if not client.call("GET", "/tokens/verify").get("success"):
        raise ToolError(2, "token verification failed: check that the token has not expired and has the Zero Trust permissions")
    print("login methods (onetimepin must be present)")
    idps = client.call("GET", "/access/identity_providers").get("result") or []
    for i in idps:
        print(f"  idp: {i.get('name')} type={i.get('type')} id={i.get('id')}")
    otp = [i["id"] for i in idps if i.get("type") == "onetimepin"]
    print("existing Access app")
    app = client.find_app(host)
    if app:
        print(f"  app: {app.get('name')} domain={app.get('domain')} "
              f"dest={[d.get('uri') for d in app.get('destinations') or []]} id={app.get('id')}")
    else:
        print(f"  no app for {host}")

    if cmd == "check":
        return 0
    if cmd == "emails":
        if app:
            for p in client.call("GET", f"/access/apps/{app['id']}/policies").get("result") or []:
                print(f"  policy {p.get('name')} decision={p.get('decision')} allowed={emails_from_policy(p)}")
        return 0
    if cmd == "harden":
        if not app:
            raise ToolError(4, f"no Access app found for {host}; run apply first")
        cur = client.call("GET", f"/access/apps/{app['id']}")["result"]
        body = {k: v for k, v in cur.items() if k not in ("id", "created_at", "updated_at", "aud", "uid", "policies")}
        body.update(session_duration=session, same_site_cookie_attribute="lax",
                    enable_binding_cookie=True, http_only_cookie_attribute=True)
        body["policies"] = [{"id": p["id"], "precedence": p.get("precedence", i + 1)}
                            for i, p in enumerate(cur.get("policies") or [])]
        if not body["policies"]:
            raise ToolError(4, "no existing policy was read; stopping so the allowlist is not lost")
        if not client.call("PUT", f"/access/apps/{app['id']}", body).get("success"):
            raise ToolError(2, "update failed, see the errors above")
        return 0

    # apply
    if not otp:
        print("One-time PIN is not enabled, creating it")
        r = client.call("POST", "/access/identity_providers", {"name": "One-time PIN", "type": "onetimepin", "config": {}})
        if not r.get("success"):
            raise ToolError(2, "could not create One-time PIN, see the errors above")
        otp = [r["result"]["id"]]
    if app is None:
        print("creating app")
        r = client.call("POST", "/access/apps", {
            "name": name, "type": "self_hosted", "domain": host,
            "destinations": [{"type": "public", "uri": host}, {"type": "public", "uri": "*." + host}],
            "session_duration": "720h", "allowed_idps": otp, "auto_redirect_to_identity": True,
            "policies": [policy_body(emails)]})
        if not r.get("success"):
            raise ToolError(2, "could not create the app, see the errors above")
        print(f"  app created, id={r['result']['id']} (run harden next)")
    else:
        print(f"app already exists, id={app['id']}; updating the allowlist")
        pols = client.call("GET", f"/access/apps/{app['id']}/policies").get("result") or []
        for p in pols:
            print(f"  current allowlist before replacing: {emails_from_policy(p)}")
        if pols:
            r = client.call("PUT", f"/access/apps/{app['id']}/policies/{pols[0]['id']}", policy_body(emails))
        else:
            r = client.call("POST", f"/access/apps/{app['id']}/policies", policy_body(emails))
        if not r.get("success"):
            raise ToolError(2, "could not update the allowlist, see the errors above")
    return 0


def build_parser():
    ap = argparse.ArgumentParser(prog="cf_private_site.py",
                                 description="Manage the Cloudflare Access allowlist in front of a Pages site. "
                                             "Requires the environment variable CF_ENV_FILE (see the file header).")
    ap.add_argument("cmd", choices=["check", "emails", "apply", "harden"])
    ap.add_argument("emails", nargs="*", help="for apply: every email that may enter (replaces the whole list)")
    ap.add_argument("--host", required=True, help="for example example.pages.dev")
    ap.add_argument("--session", default="168h", help="session length for harden (default 168h, 7 days)")
    return ap


def main(argv=None, environ=None, opener=None):
    environ = os.environ if environ is None else environ
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return run_selftest()
    a = build_parser().parse_args(argv)  # bad arguments exit 2 through argparse
    try:
        host = valid_host(a.host)
        if not host:
            raise ToolError(2, f"--host must be a bare host name such as example.pages.dev, got: {a.host!r}")
        emails = []
        if a.cmd == "apply":
            emails, invalid = parse_emails(a.emails)
            if invalid:
                raise ToolError(2, f"not valid email addresses: {', '.join(invalid)}")
            if not emails:
                raise ToolError(2, "apply needs at least one email")
        token, account = get_credentials(environ)
        return run_command(Client(token, account, opener), a.cmd, host, emails, a.session)
    except ToolError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return e.code


# ---------- selftest ----------

def run_selftest():
    import contextlib
    import subprocess
    import tempfile

    results = []

    def check(cond, label):
        results.append(bool(cond))
        print(f"[{'PASS' if cond else 'FAIL'}] {label}")

    def fake_cloud(state, token_ok=True, token_status=200, network_down=False):
        """Return (opener, calls). state is a dict the fake API reads and updates."""
        calls = []

        def opener(req, timeout=30):
            if network_down:
                raise urllib.error.URLError("fake network down")
            method = req.get_method()
            path = req.full_url.split("/accounts/acct123", 1)[1]
            body = json.loads(req.data) if req.data else None
            calls.append((method, path, body))

            def ok(result):
                return io.BytesIO(json.dumps({"success": True, "errors": [], "result": result}).encode())

            if path == "/tokens/verify":
                if not token_ok:
                    raise urllib.error.HTTPError(req.full_url, token_status, "forbidden", {},
                                                 io.BytesIO(b'{"success": false, "errors": [{"code": 1000}]}'))
                return ok({"status": "active"})
            if path == "/access/identity_providers" and method == "GET":
                return ok(state["idps"])
            if path == "/access/identity_providers" and method == "POST":
                state["idps"].append({"id": "idp-new", "name": "One-time PIN", "type": "onetimepin"})
                return ok({"id": "idp-new"})
            if path == "/access/apps" and method == "GET":
                return ok(state["apps"])
            if path == "/access/apps" and method == "POST":
                state["apps"].append({"id": "app-new", "name": body["name"], "domain": body["domain"],
                                      "destinations": body["destinations"]})
                return ok({"id": "app-new"})
            m = re.match(r"^/access/apps/([^/]+)(/policies(?:/([^/]+))?)?$", path)
            if m:
                if m.group(2) and method == "GET":
                    return ok(state.get("policies", []))
                if m.group(2):
                    return ok({"id": m.group(3) or "pol-new"})
                if method == "GET":
                    return ok(state["app_detail"])
                if method == "PUT":
                    return ok({})
            raise AssertionError(f"unexpected fake API call: {method} {path}")

        return opener, calls

    def new_state(with_otp=True, with_app=False, with_policy=True):
        st = {"idps": [{"id": "idp-1", "name": "One-time PIN", "type": "onetimepin"}] if with_otp else [],
              "apps": [], "policies": []}
        if with_app:
            st["apps"] = [{"id": "app-1", "name": "demo", "domain": "demo.example.pages.dev",
                           "destinations": [{"uri": "demo.example.pages.dev"}, {"uri": "*.demo.example.pages.dev"}]}]
            st["app_detail"] = {"id": "app-1", "aud": "x", "uid": "y", "name": "demo", "domain": "demo.example.pages.dev",
                                "policies": [{"id": "pol-1", "precedence": 1}] if with_policy else [],
                                "session_duration": "720h"}
            if with_policy:
                st["policies"] = [{"id": "pol-1", "name": "invited emails", "decision": "allow",
                                   "include": [{"email": {"email": "old@example.com"}}]}]
        return st

    env_ok = {"CF_ENV_FILE": ""}
    HOST = "demo.example.pages.dev"

    def drive(argv, state, **kw):
        opener, calls = fake_cloud(state, **kw)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = main(argv, environ=env_ok, opener=opener)
        return rc, calls, out.getvalue(), err.getvalue()

    with tempfile.TemporaryDirectory(prefix="cf_private_site_selftest_") as tmp:
        # credentials file with fake values only
        good = os.path.join(tmp, "good.cfg")
        with open(good, "w", encoding="utf-8") as f:
            f.write('# comment\n\nCLOUDFLARE_API_TOKEN="fake-token-value"\nCLOUDFLARE_ACCOUNT_ID=acct123\n')
        half = os.path.join(tmp, "half.cfg")
        with open(half, "w", encoding="utf-8") as f:
            f.write("CLOUDFLARE_API_TOKEN=fake-token-value\n")
        env_ok["CF_ENV_FILE"] = good

        # --- credentials, through the real script in a subprocess (no network can happen: it stops before any call) ---
        script = os.path.abspath(__file__)
        base_env = {k: v for k, v in os.environ.items() if k != "CF_ENV_FILE"}

        def sub(extra_env, args):
            r = subprocess.run([sys.executable, "-I", script] + args, capture_output=True, text=True,
                               env={**base_env, **extra_env}, timeout=60)
            return r.returncode, r.stdout + r.stderr

        rc, text = sub({}, ["check", "--host", HOST])
        check(rc == 5 and "CF_ENV_FILE is not set" in text and "Traceback" not in text,
              "CF_ENV_FILE unset -> clear error, exit 5, no traceback")
        rc, text = sub({"CF_ENV_FILE": os.path.join(tmp, "nope.cfg")}, ["check", "--host", HOST])
        check(rc == 5 and "cannot be read" in text and "Traceback" not in text, "CF_ENV_FILE points at a missing file -> exit 5")
        rc, text = sub({"CF_ENV_FILE": half}, ["check", "--host", HOST])
        check(rc == 5 and "CLOUDFLARE_ACCOUNT_ID" in text and "fake-token-value" not in text,
              "credentials file missing a key -> exit 5, names the key, never echoes the token")

        # --- pure helpers ---
        parsed = load_env(good)
        check(parsed == {"CLOUDFLARE_API_TOKEN": "fake-token-value", "CLOUDFLARE_ACCOUNT_ID": "acct123"},
              "load_env skips comments and blank lines and strips quotes")
        exp = os.path.join(tmp, "exp.cfg")
        with open(exp, "w", encoding="utf-8") as f:
            f.write("export CLOUDFLARE_API_TOKEN=fake-token-value\nexport CLOUDFLARE_ACCOUNT_ID=acct123\n")
        check(load_env(exp) == parsed, "load_env accepts lines written as export KEY=value")
        check(valid_host("Demo.Example.Pages.dev") == HOST, "valid_host lowercases a good host")
        check(all(valid_host(h) is None for h in ["https://x.pages.dev", "x.pages.dev/path", "*.x.pages.dev", "x", "", "x.pages.dev:8080", "a b.pages.dev"]),
              "valid_host rejects scheme, path, wildcard, bare word, empty, port, space")
        emails, invalid = parse_emails(["A@Example.com, b@example.com", "a@example.com;c@example.com"])
        check(emails == ["a@example.com", "b@example.com", "c@example.com"] and invalid == [],
              "parse_emails splits on comma/semicolon/space, lowercases, drops duplicates")
        emails, invalid = parse_emails(["good@example.com", "not-an-email", "@x.com", "a@b"])
        check(emails == ["good@example.com"] and invalid == ["not-an-email", "@x.com", "a@b"],
              "parse_emails reports invalid addresses")
        check(policy_body(["a@example.com"]) == {"name": "invited emails", "decision": "allow",
                                                 "include": [{"email": {"email": "a@example.com"}}]},
              "policy_body shape")
        check(emails_from_policy(policy_body(["a@example.com", "b@example.com"])) == ["a@example.com", "b@example.com"],
              "emails_from_policy reads the addresses back")

        # --- find_app ---
        st = new_state(with_app=True)
        opener, _ = fake_cloud(st)
        cl = Client("t", "acct123", opener)
        with contextlib.redirect_stdout(io.StringIO()):
            check(cl.find_app(HOST) is not None, "find_app matches by domain")
            st["apps"].append({"id": "app-null", "name": "legacy", "domain": "legacy.example.pages.dev", "destinations": None})
            check(cl.find_app("legacy.example.pages.dev").get("id") == "app-null" and cl.find_app("zzz.example.pages.dev") is None,
                  "find_app copes with destinations: null")
            check(cl.find_app("other.example.pages.dev") is None,
                  "find_app ignores an app that has the same name but another domain")
            check(cl.find_app("x.demo.example.pages.dev") is None, "find_app returns None when nothing matches")

        # --- commands against the fake API ---
        rc, calls, out, _ = drive(["check", "--host", HOST], new_state(with_app=True))
        check(rc == 0 and all(c[0] == "GET" for c in calls), "check is read-only (GET calls only)")
        rc, calls, out, _ = drive(["emails", "--host", HOST], new_state(with_app=True))
        check(rc == 0 and "old@example.com" in out and all(c[0] == "GET" for c in calls), "emails lists the allowlist, read-only")

        rc, calls, out, _ = drive(["apply", "--host", HOST, "A@example.com", "b@example.com"], new_state(with_otp=False))
        post_app = [c for c in calls if c[0] == "POST" and c[1] == "/access/apps"]
        body = post_app[0][2] if post_app else {}
        check(rc == 0 and any(c[0] == "POST" and c[1] == "/access/identity_providers" for c in calls),
              "apply on a fresh account creates One-time PIN first")
        check([d["uri"] for d in body.get("destinations", [])] == [HOST, "*." + HOST] and body.get("allowed_idps") == ["idp-new"],
              "apply creates the app with both destinations (host and *.host) and the new login method")
        check(emails_from_policy(body.get("policies", [{}])[0]) == ["a@example.com", "b@example.com"],
              "apply puts the normalized emails into the Allow policy")

        rc, calls, out, _ = drive(["apply", "--host", HOST, "new@example.com", "old@example.com"], new_state(with_app=True))
        puts = [c for c in calls if c[0] == "PUT"]
        check(rc == 0 and not any(c[0] == "POST" for c in calls) and len(puts) == 1
              and emails_from_policy(puts[0][2]) == ["new@example.com", "old@example.com"],
              "apply on an existing app replaces the whole list through one PUT, creates nothing")

        # an app with the same name as the new site but protecting another domain must stay untouched
        other = new_state(with_app=True)
        other["apps"][0].update(name="blog", domain="blog.mycompany.example", destinations=[{"uri": "blog.mycompany.example"}])
        rc, calls, _, _ = drive(["apply", "--host", "blog.pages.dev", "friend@example.com"], other)
        check(rc == 0 and not any(c[0] == "PUT" for c in calls)
              and any(c[0] == "POST" and c[1] == "/access/apps" for c in calls),
              "apply for blog.pages.dev creates a new app and never rewrites another site's app that is also called blog")
        rc, calls, out, _ = drive(["apply", "--host", HOST, "new@example.com"], new_state(with_app=True))
        check("current allowlist before replacing: ['old@example.com']" in out, "apply on an existing app prints the old allowlist first")

        rc, calls, _, err = drive(["apply", "--host", HOST, "bad-address"], new_state())
        check(rc == 2 and calls == [] and "bad-address" in err, "apply with an invalid email -> exit 2 before any API call")
        rc, calls, _, err = drive(["apply", "--host", HOST], new_state())
        check(rc == 2 and calls == [], "apply with no email -> exit 2 before any API call")
        rc, calls, _, err = drive(["check", "--host", "https://demo.example.pages.dev/"], new_state())
        check(rc == 2 and calls == [], "a URL as --host -> exit 2 before any API call")

        rc, calls, _, _ = drive(["harden", "--host", HOST], new_state(with_app=True))
        puts = [c for c in calls if c[0] == "PUT"]
        b = puts[0][2] if puts else {}
        check(rc == 0 and b.get("session_duration") == "168h" and b.get("same_site_cookie_attribute") == "lax"
              and b.get("enable_binding_cookie") is True and b.get("http_only_cookie_attribute") is True
              and b.get("policies") == [{"id": "pol-1", "precedence": 1}] and "aud" not in b and "id" not in b,
              "harden sets session, SameSite Lax, Binding cookie, HttpOnly, keeps policy ids, strips read-only fields")
        rc, calls, _, err = drive(["harden", "--host", HOST], new_state(with_app=True, with_policy=False))
        check(rc == 4 and not any(c[0] == "PUT" for c in calls), "harden with no policy -> exit 4 and no PUT (allowlist protected)")
        rc, calls, _, err = drive(["harden", "--host", HOST], new_state())
        check(rc == 4, "harden without an app -> exit 4")

        rc, calls, _, err = drive(["check", "--host", HOST], new_state(), token_ok=False, token_status=403)
        check(rc == 2 and len(calls) == 1 and "token verification failed" in err, "token rejected (HTTP 403) -> exit 2, stops after one call")
        rc, calls, _, err = drive(["check", "--host", HOST], new_state(), network_down=True)
        check(rc == 2 and "network error" in err, "network failure -> exit 2, no traceback")

        # --- argparse ---
        for argv_bad, label in [(["bogus", "--host", HOST], "unknown command"), (["check"], "missing --host")]:
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    main(argv_bad, environ=env_ok)
                code = None
            except SystemExit as e:
                code = e.code
            check(code == 2, f"{label} -> exit 2")

        # --- text hygiene ---
        src = open(script, encoding="utf-8").read()
        check("example.pages.dev" in build_parser().format_help() or "example.pages.dev" in src, "help/example uses example.pages.dev")
        needles = ["/Us" + "ers/", "Desk" + "top", "expand" + "user"]
        check(not any(n in src for n in needles),
              "no hard-coded user path or default credential location in the source")

    passed = sum(results)
    print(f"\nselftest result: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

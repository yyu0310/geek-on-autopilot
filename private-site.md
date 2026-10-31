---
name: private-site
description: Publish a static website or HTML page as a private, invite-only site. Cloudflare Pages direct upload plus an Access allowlist, so only invited emails that enter a one-time code can get in. Covers content audit, lock-first deployment, lock verification, independent review, scheduled updates, and adding people later. Use when the user wants to put an HTML or data page online for friends, build an invite-only site, or restrict who can view it.
---

# /private-site: put a static site behind an invite list

> The approach is settled, so don't reopen the comparison: Cloudflare Pages direct upload plus a Zero Trust Access policy. Apps Script web apps are out: they can't read the email of a consumer-account visitor, they have to run as the visitor, friends see an "unverified app" warning, and you would write the allowlist yourself. GitHub Pages plus a password is out too: the source is public.

## Shared tools

Both scripts live in the repo root and use only the standard library (plus `curl` for the shell one). The commands below assume you run them from the repo root. Otherwise, use the full path.

| Tool | What it does |
| --- | --- |
| `cf_private_site.py` | Manages Access: `check`, `emails`, `apply <emails>` (replaces the whole list), `harden`. Always pass `--host X.pages.dev` and run it as `python3 -I`. Needs the environment variable `CF_ENV_FILE` (see Step 3) |
| `site_lock_check.sh` | About 40 curl probes that an anonymous visitor gets nothing: `bash site_lock_check.sh <host> '<string only the page contains>' [deploy-url-file]`. For a multi-page site set `EXTRA_PATHS='/page2.html /b'`. Run it only against a site you own. |
| Review prompt | A template for an independent LLM review, at the end of this file |

Each script has `--selftest` (no network, a fake API or a fake curl).

## Step 1: Scope check (before you start, 3 minutes)

1-1 **Is the content purely static** (HTML, CSS, JS, and images, with no backend, database, or writes)? If yes, use this SOP. If there is a backend or stored data, stop and ask the user: that needs Workers plus D1 and a separate design.

1-2 **Ask the user three things.** Who may view it: an allowlist of emails, or just the user if none is given. What the URL should be called: a project name in lowercase letters, digits, and hyphens, which gives `<name>.pages.dev`. Whether the data will update, which leads to Step 7.

1-3 **Does the site have an owner's version and a friends' version** (balances, personal data, local links)? If yes, do the publish-version conversion in Step 2-4.

## Step 2: Content audit before publishing (required, nothing goes up unread)

2-1 Mechanical scan: search the HTML you plan to publish for your username, absolute home-directory paths and other private paths, your own name, `api_key`, `token`, `Authorization`, `Bearer`, `password`. Every term must return 0 hits.

2-2 Extract the plain text (drop script and style) and read it yourself for personal information: amounts, point balances, personal data, names.

2-3 Look at external resources and links. A public CDN (jsdelivr and similar) is fine. A relative link to a local `.md` file becomes a dead link online, so turn it into plain text.

2-4 **If something has to be hidden, do a publish-version conversion.** Leave the source file alone. The deploy script produces the publish version under `public/` from the source on every run, then uses `assert` to check that sensitive strings are gone and that the number of replacements is what you expect. If the structure of the source changes, the script stops and raises an alert instead of quietly publishing a balance. Note that values derived from a balance ("how many items can I afford", "credit left") leak too: remove the whole block, not only the digits. Constants in the code also go, because view-source shows them.

2-5 After editing, check the embedded JavaScript with `node --check`, then confirm the page header still reads well.

## Step 3: Accounts and credentials (the user does this, the assistant never touches a credential)

3-1 The Cloudflare account needs 2FA (the assistant can't see it, so the user confirms). Use the Zero Trust Free plan (50 users). The first visit asks for a team name, which becomes the login page URL. It can be renamed under Zero Trust Settings, so pick one that is easy to recognize.

3-2 **Two separate tokens.** The deploy token only needs Account / Cloudflare Pages / Edit, and lives wherever the deploy runs. The settings token uses the Zero Trust template (Access Apps and Policies Edit, plus Edit on Organizations, Identity Providers, and Groups, so that `apply` can create One-time PIN when it is missing) and lives only on the machine you manage Access from. If you already have them, reuse them. Tokens can expire, so when a script returns 403, suspect expiry first. If a permission is missing, edit the same token to add it. The value stays the same.

3-3 **Where the credential files go.** Each token goes in its own env file (`CLOUDFLARE_API_TOKEN=...` and `CLOUDFLARE_ACCOUNT_ID=...`), kept outside any repository and outside any folder an AI tool can read. The user creates and copies these files. `cf_private_site.py` reads the settings file through the **required** environment variable `CF_ENV_FILE`. It has no default location, and without the variable it prints an error and exits 5. The deploy script loads the deploy env file in its own way. Credentials are read only by programs: the assistant never opens a credential file, never prints a token, and never pastes one into the conversation. If a permission hook or sandbox blocks a command, follow the block message instead of working around it, and ask the user to run the command in their own terminal.

## Step 4: Create the project, lock first

4-1 Create the Pages project: `wrangler pages project create <name> --production-branch main` (direct upload, no git).

4-2 **Lock before the first deployment, so there is never a public window**: `CF_ENV_FILE=<settings env file> python3 -I cf_private_site.py apply --host <name>.pages.dev <emails>`. It creates One-time PIN if missing, and the app covers both the production URL and `*.<name>.pages.dev`. Then run `harden` (7-day session, Binding cookie, SameSite Lax, HttpOnly).

4-3 Run `check` and confirm both destinations of the app exist. Don't rely on the Pages dashboard's Enable access policy button: it locks only the preview URLs and leaves the production URL public.

## Step 5: Deploy

5-1 Use an ASCII path for the publish folder (`public/index.html`). Install wrangler locally and pin the version (`npm i --save-exact wrangler@<version>`) instead of fetching the latest with `npx` every time. A scheduled job often has a minimal PATH, so export what the script needs inside the script.

5-2 Deploy with `wrangler pages deploy public --project-name <name> --branch main --commit-dirty=true`, with the two environment variables loaded by your script from the deploy env file. Direct upload doesn't use the monthly 500-build quota.

5-3 Run it once by hand and note the deployment URL.

## Step 6: Verify (no evidence, no "done")

6-1 Run `bash site_lock_check.sh <host> '<string only the page contains>' [deploy-url-file]` and require exit 0 with `fail=0`. The marker is an egrep (ERE) pattern, so escape characters such as `(`, `+`, and `[` (`'C\+\+'`). An invalid pattern is refused with exit 2. Every response is judged by status code too: a 2xx answer counts as a failure (except the Cloudflare paths below), and so does a host that doesn't answer (exit 6), so a mistyped host can't pass. Any other status code also counts as a failure and needs a manual look. Get the deployment URLs from `wrangler pages deployment list --project-name <name> --json` (the `Deployment` field), write them one per line to a file, and pass that file. The script refuses any URL outside your host, and a deployment URL that doesn't answer counts as a failure. A 200 from `/cdn-cgi/trace` or `/cdn-cgi/access/*` is standard Cloudflare content, and the output marks it `exempt_200`.

6-2 **Independent attack check.** Give a fresh-context agent the host and have it try to get around the lock with read-only curl only: path variants, methods, forged headers, guessed branch subdomains. It doesn't log in, guess a code, or touch the login submit endpoint, and it only tests your own site. Collect a conclusion and a table, nothing more.

6-3 **Independent LLM review.** Fill in the placeholders of the prompt template at the end of this file, save it as a temp file, and give it to a different, independent LLM that can browse the web. Allow a generous timeout, since a thorough run can take around ten minutes. Run its curl list yourself. Treat any external link it cites as unverified until you have opened it, and have it report risks in two groups: "evidence seen" and "unverified".

6-4 **The owner logs in with an allowlisted email** and checks the page, filters, and layout. The assistant can't do this for you. If you keep getting sent back to the login page after logging in, turn off the Binding cookie.

6-5 Run the Step 2-1 scan again on the published files.

## Step 7: Sites whose data changes

If the data updates, run the deploy script on a schedule.

## Step 8: Day-to-day management

8-1 **Adding or removing people**: `cf_private_site.py apply --host <host> <all emails>` replaces the whole list, so always write everyone, then read it back with `emails` to confirm. The output of `apply` and `emails` contains the invited emails, so run them in your own terminal when needed and don't paste the output anywhere public.

8-2 Sessions last 7 days, and on the free plan Access keeps login logs for only 24 hours. Remove friends who stop using the site, and look at Zero Trust → Logs for a moment in the days after adding someone.

8-3 An invited person can save or forward the page. Technically that can't be stopped, so agree on it with them up front.

## Pitfalls (symptom, cause, what to do)

| Symptom | Cause | What to do |
| --- | --- | --- |
| Clicked Enable access policy in the Pages dashboard and the production URL is still public | It only locks preview URLs | Create the app with `apply`, and make sure both destinations exist |
| Added one email and the earlier people can't get in | `apply` replaces the whole list | Always write everyone, then confirm with `emails` |
| The login page URL is a random string | A random team name was assigned when Zero Trust was enabled | Rename it in Zero Trust Settings. The login link changes, the allowlist doesn't |
| `/cdn-cgi/trace` returns 200 | Cloudflare node info that every site returns | Nothing to fix, the check marks it exempt |
| After login you keep landing on the login page again | The Binding cookie doesn't fit the browser setup | Check before `harden`. If it happens, turn off the Binding cookie first |
| wrangler misbehaves on a path with non-ASCII characters | Tool limitation | Use an ASCII publish folder |
| A scheduled job can't find node or wrangler | The job's PATH is minimal | Export PATH inside the script and install wrangler locally with a pinned version |

## Appendix: prompt template for the independent review

Copy it to a temp file and replace `{HOST}`, `{TEAM}`, `{CONTENT}`, and `{DEPLOY}` with this site's real values. Don't put in tokens, allowlist emails, or any credential.

```text
You are a red-team consultant. The site below is mine and I authorize testing it. Before friends start using it, I want every possible path by which someone who is NOT on the allowlist could still get the page content. Answer in English. Search the official documentation and publicly known bypass cases (CVEs, security advisories, community reports) as far as you can, and attach a source URL to every claim.

SYSTEM FACTS (all of them)
- Content: {CONTENT} (for example: a 2 MB single-file static HTML page, no backend, no API, no database, no Pages Functions). The risks are "seen by someone who wasn't invited" and "forwarded".
- Hosting: a Cloudflare Pages project, direct upload (no git), production URL https://{HOST}, plus https://<hash>.{HOST} for every deployment.
- Lock: Cloudflare Zero Trust Access (Free plan), team name {TEAM}, a self-hosted application with destinations {HOST} and *.{HOST}. The only login method is One-time PIN. The only policy is Allow plus an Emails allowlist. Session 7 days, Binding cookie on, SameSite Lax, HttpOnly on. There is no Bypass or Service Auth policy and no custom domain.
- Updates: {DEPLOY} (for example, a scheduled job deploys with wrangler using an API token limited to Pages Edit).
- Already tested (anonymous, curl): the production URL and path variants, letter case, HEAD/POST/PUT/OPTIONS, forged Access headers and X-Forwarded-*, a forged Host, deployment hash URLs, and common branch subdomains. Everything redirected to the login domain or was refused, and 0 content leaked.

WHAT I NEED FROM YOU
1. A threat model in four groups, listing every path by which a non-allowlisted person could see the content:
   a. Known bypasses or design gaps in Cloudflare Access and Pages themselves (how far *.pages.dev aliases and preview URLs are covered, whether old deployments stay reachable, the /cdn-cgi/access/ endpoints, JWT and cookie validation, the OTP flow such as email normalization, letter case, plus-address aliases, homoglyphs, resend and brute-force limits, differences on the Free plan).
   b. Configuration mistakes: is there a hole in the current setup, and which common misconfigurations should I self-check.
   c. Supply chain and credentials: ways an API token can leak, a local wrangler install, deploy scripts, the Cloudflare account itself (2FA, members).
   d. People: an allowlisted person forwarding the link or a screenshot, an email account being taken over, session length.
2. For each item: likelihood (high / medium / low), impact, how I verify it, and how I fix it.
3. Turn everything that can be checked from outside, anonymously, with plain HTTP requests, into a curl test list that only touches {HOST} and its subdomains. Don't include any step that sends an OTP email to a third party, and no brute forcing. I will run it myself and report back.
4. You may use your web-fetch tool for anonymous GET requests against https://{HOST}/ and the public endpoints under https://{HOST}/cdn-cgi/access/. Don't try to log in, don't guess codes, don't touch any domain that isn't this site. Report exactly what you see. If you see nothing, say so. Don't invent anything.

OUTPUT FORMAT
Conclusion first: "Found N risks worth handling". Then a risk table (id, group, likelihood, impact, how to verify, fix), then the curl test list. Every "verified" claim needs evidence you actually saw. Otherwise mark it "unverified".
```

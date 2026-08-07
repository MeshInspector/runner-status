# runner-status

A status page for the MeshInspector org's self-hosted GitHub Actions runners:
**https://meshinspector.github.io/runner-status/**

## What gets published

Only two fields per runner come from the GitHub API — `status` (online/offline) and
`busy`. Everything else on the page comes from [`allowlist.json`](allowlist.json), which
is also the publication gate: a runner not listed there is not published at all, so a
newly registered machine never appears by accident.

Allowlisted runners are shown under their real names. Runner **labels are never
published**, and some runners are intentionally left off the list.

To add a runner, edit `allowlist.json` — `name` must match the runner's real name exactly
(case-insensitive); `os` is `windows` | `linux` | `macos`; `spec` is free text. Optional
`display` overrides the name on the page for anything you would rather not publish
verbatim. If an allowlisted runner disappears from the org it shows as "not registered"
rather than vanishing silently.

## Setup

1. **Create a GitHub App** in the org (Settings → Developer settings → GitHub Apps → New).
   - Organization permission: **Self-hosted runners → Read-only**. Nothing else — no
     repository permissions at all.
   - Uncheck "Webhook → Active".
   - Install it on the MeshInspector org.
2. Generate a private key, then here:
   - repo **variable** `RUNNER_STATUS_APP_CLIENT_ID` — the App's client id (`Iv23…`);
     `app-id` is deprecated in `create-github-app-token`, and the client id is
     public metadata anyway (`gh api apps/<slug>`), so it is not a secret.
   - repo **secret** `RUNNER_STATUS_APP_PRIVATE_KEY` — the whole `.pem`.
3. Run **Publish runner status** manually with `deploy` **off**, download the `site`
   artifact, and check `runners.json` — that file is exactly what goes public.
4. Settings → Pages → Source: **GitHub Actions**.
5. Re-run with `deploy` on. The site lands at
   `https://meshinspector.github.io/runner-status/`.

## Refresh rate

The workflow runs every 10 minutes. GitHub's scheduler is best-effort and often fires
late under load, which is why the page states when its snapshot was taken instead of
pretending to be live. Scheduled workflows are also disabled automatically after 60 days
without repository activity.

For a genuinely live page you would need a server holding the App key (a Lambda function
URL with a short cache, say). That is a public unauthenticated endpoint to own and
rate-limit; the snapshot approach avoids it.

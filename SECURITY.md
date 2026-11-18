# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 2.x (latest release) | Yes |
| 1.x | No |

Security fixes go into the newest 2.x release as a patch version (for example 2.0.1 to 2.0.2). Run the latest image, `dhomoney/watch-tracker:latest` or the newest version tag, to get them. The 1.x images (`dhomoney/watch-tracker-backend` and `dhomoney/watch-tracker-frontend`) no longer receive updates.

## Reporting a vulnerability

Please report security problems privately, not in a public issue, pull request or discussion.

1. Open the repository's [Security tab](https://github.com/Homoney/watch_collection_tracker/security).
2. Click **Report a vulnerability** ([direct link](https://github.com/Homoney/watch_collection_tracker/security/advisories/new)).
3. Describe the problem, the version or image tag, and the steps to reproduce it.

Only the maintainers can see the report.

## What to expect

- This is a personal project maintained on a best-effort basis. We aim to acknowledge a report within a week.
- We confirm the problem, agree on a fix with you in the private report, and release it as a patch version.
- After the fix is released we publish a security advisory, crediting you if you wish.
- Please give us a reasonable time to release a fix before you disclose the problem publicly.

## Scope

In scope: the code in this repository and the published `dhomoney/watch-tracker` image.

Out of scope: problems in your own deployment (for example a reverse proxy, TLS setup or host), and findings that need an already compromised server or admin account.

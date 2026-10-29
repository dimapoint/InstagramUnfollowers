---
name: run-instagramunfollowers
description: Build, run, and drive InstagramUnfollowers (the dist/dist.js console script). Use when asked to run or start the app, test the scan or unfollow flow, check that a change works, or take a screenshot of its UI, without touching a real Instagram account.
---

The app is a script pasted into the DevTools console on instagram.com, so there is no server to start. Agents drive it with `.claude/skills/run-instagramunfollowers/driver.py`: headless Chromium (Python Playwright) loads `dist/dist.js` on a **fake `https://www.instagram.com/`**, mocks the friendships API and the GraphQL unfollow mutation, runs Scan → select → Unfollow, and checks the requests the app sends. No request ever reaches Instagram: unmocked ones are aborted and reported.

Paths are relative to the repo root. Verified on Windows 11 with Git Bash, Bun 1.4.3, Python 3.14 and Playwright 1.64.

## Prerequisites

```bash
python -m pip install playwright
python -m playwright install chromium
```

## Build

```bash
bun install
bun run build
```

`bun run build` type-checks with `tsc --noEmit`, writes `dist/dist.js` and copies it to the clipboard through PowerShell. The driver reads `dist/dist.js`, so **rebuild after every `src/` change** or you'll be testing the old bundle.

## Run (agent path)

```bash
python .claude/skills/run-instagramunfollowers/driver.py
python .claude/skills/run-instagramunfollowers/driver.py --select 3
python .claude/skills/run-instagramunfollowers/driver.py --broken --select 3
```

- `--select N`: how many non-followers to unfollow (default 2, at most 3).
- `--broken`: the mutation answers with a 200 HTML page, which is what Instagram does for routes it doesn't serve to the web client. Every unfollow must then show `Failed to unfollow`; before the fix, that page counted as a success.
- `--out DIR`: where screenshots go (default `%TEMP%\iu-shots`, i.e. `C:\Users\<you>\AppData\Local\Temp\iu-shots`).

It takes about 2 s, prints a JSON summary and then `OK` (exit 0) or `FAIL` (exit 1):

```
"results_shown": ["dani.nosigue", "eli.nosigue", "fede.nosigue"],
"unfollow_requests": [{"target_user_id": "4", "doc_id": "27789106940691111", "fb_dtsg": "mockdtsg", "csrf": "mockcsrf"}, ...],
"unexpected_requests": [],
"console_errors": [],
"log": ["All DONE!", "Unfollowed dani.nosigue [1/2]", "Unfollowed eli.nosigue [2/2]"]
```

It fails when the results aren't exactly the 3 non-followers, the number of `/api/graphql` POSTs is off, a POST lacks a valid `target_user_id` or the page's `fb_dtsg`, the log doesn't have one `Unfollowed` line per selected user (`Failed to unfollow` with `--broken`), the app requests a URL the mock doesn't serve, or the console shows an error. Screenshots: `1-launch.png` (launch screen), `2-scan.png` (results), `3-unfollow.png` (finished queue). Open them and look.

`unfollowUser()` (`src/utils/utils.ts`) only reports success after Instagram confirms it: the mutation's `friendship_status` and a search of the following list (`/following/?query=<username>`). The mock answers that search from the users it has already unfollowed, and reads `fb_dtsg`/`lsd` from a `<script>` in the stub page's `<head>`. The fake account is viewer `100`: followers are users 1-3 and following is users 1-6, so 4-6 (`*.nosigue`) are the non-followers. To exercise other API behavior (an action block on the mutation, pagination with `next_max_id`, `has_more`), edit `handle()` in `driver.py`. Every mocked endpoint is in that one function.

## Run (human path)

`bun run build`, open instagram.com logged in, paste the clipboard into the DevTools console. Real account, real unfollows: never do this from an agent.

## Test

There is no test suite. `bun run build` (tsc) plus the driver's `OK` is the check. `bunx eslint src` has ~300 pre-existing errors, so only read it for the files you touched.

## Gotchas

- **The localhost preview skips everything that matters.** On `localhost`/`127.0.0.1` (`isLocalPreview` in `src/main.tsx`) the app shows fake users, and the scan and unfollow effects `return` right away, so no request is ever sent. Use it only for pure layout work. The driver uses Playwright routing to serve the page as `www.instagram.com` instead, which runs the real code paths.
- **Default timings make a run take minutes.** The app waits 4 s between unfollows and 5 min after every five. The driver seeds `localStorage.iu_timings` with tiny values (0-100 ms) before load.
- **Mojibake if the page has no charset.** Serving `dist.js` without `charset=utf-8` decodes the UTF-8 bundle as windows-1252: `Â Verified`, `â˜…`, `Ã—` all over the UI. That's a harness bug, not an app bug (Instagram's page is UTF-8). The driver's HTML stub sets `<meta charset="utf-8">`.
- **Checkboxes are disabled while scanning.** Wait for `.account-checkbox:not([disabled])` before selecting. `button.unfollow` opens a `confirm()`, which the driver auto-accepts.
- **The unfollow log pads usernames with `&nbsp;`.** A cp1252 Windows console prints them as `�`. The driver collapses whitespace before printing.
- **An action block stops the whole queue.** `unfollowUser()` returns `blocked` for HTTP 429, `spam: true` or an error matching `feedback_required|checkpoint|action_blocked|try again later|rate limit`, and the loop `break`s on it. `All DONE!` never shows up after that, so the driver's `wait_for_selector(".unfollow-log-container .clr-green")` times out after 30 s. When you mock a block, replace that wait with `page.wait_for_timeout(2000)`. Any other error (a plain 400, HTML, a GraphQL `errors`) counts as `failed` and the queue moves on.
- **The mock only proves what the app sends.** It can't tell you whether Instagram still accepts the mutation: `INSTAGRAM_UNFOLLOW_DOC_ID` in `src/constants/constants.ts` can rotate on any Instagram deploy. If real unfollows start failing with a GraphQL error, copy the `doc_id` from the request the Unfollow button sends to `/api/graphql` (DevTools Network tab).

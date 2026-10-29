"""Drive dist/dist.js against a fake www.instagram.com in headless Chromium.

Every request is intercepted: the page, the bundle and the friendships API are
served from here, anything else is aborted, so nothing ever reaches Instagram.
Flow: launch screen -> Scan -> select non-followers -> Unfollow (GraphQL
mutation + following-list check) -> log done. Exits 1 if the unfollow
requests, the results or the console look wrong.

    python .claude/skills/run-instagramunfollowers/driver.py [--select N] [--broken] [--out DIR]
"""
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "dist" / "dist.js"
VIEWER_ID = "100"
# Followers are 1-3, following is 1-6, so 4-6 are the non-followers.
USERS = {
    str(n): name
    for n, name in enumerate(
        ["ana.sigue", "beto.sigue", "caro.sigue", "dani.nosigue", "eli.nosigue", "fede.nosigue"], start=1
    )
}
FOLLOWERS = ["1", "2", "3"]
FOLLOWING = list(USERS)
# Fast timings so the unfollow loop doesn't sleep 4s per user / 5 min every five.
TIMINGS = {
    "timeBetweenSearchCycles": 0,
    "timeToWaitAfterFiveSearchCycles": 0,
    "timeBetweenUnfollows": 100,
    "timeToWaitAfterFiveUnfollows": 100,
    "usersPerSearchCycle": 50,
}
# unfollowUser() scrapes fb_dtsg/lsd from the page HTML; the app clears <body>, so they live in <head>.
TOKENS_SCRIPT = '<script type="application/json">["DTSGInitialData",[],{"token":"mockdtsg"}],["LSD",[],{"token":"mocklsd"}]</script>'
AVATAR = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="#6366f1"/></svg>'


def raw_user(user_id):
    return {
        "pk": user_id,
        "pk_id": user_id,
        "username": USERS[user_id],
        "full_name": USERS[user_id].split(".")[0].title(),
        "profile_pic_url": f"https://www.instagram.com/mock-avatar/{user_id}.svg",
        "is_private": False,
        "is_verified": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--select", type=int, default=2, help="how many non-followers to unfollow")
    parser.add_argument("--broken", action="store_true", help="answer the unfollow mutation with a 200 HTML page; every unfollow must then fail")
    parser.add_argument("--out", default=str(Path(tempfile.gettempdir()) / "iu-shots"), help="screenshot dir")
    args = parser.parse_args()
    if not BUNDLE.exists():
        sys.exit(f"{BUNDLE} missing: run `bun run build` first")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    unfollow_requests = []
    unfollowed = set()
    unexpected = []
    console_errors = []

    def handle(route):
        req = route.request
        url = urlparse(req.url)
        path = url.path
        if url.hostname != "www.instagram.com":
            unexpected.append(req.url)
            return route.abort()
        if path == "/":
            # Without a charset the UTF-8 bundle is decoded as windows-1252 and every icon turns into mojibake.
            return route.fulfill(content_type="text/html; charset=utf-8", body='<!doctype html><html><head><meta charset="utf-8">' + TOKENS_SCRIPT + '</head><body><script src="/__dist.js"></script></body></html>')
        if path == "/__dist.js":
            return route.fulfill(content_type="application/javascript; charset=utf-8", body=BUNDLE.read_text(encoding="utf-8"))
        if path.startswith("/mock-avatar/"):
            return route.fulfill(content_type="image/svg+xml", body=AVATAR)
        match = re.fullmatch(rf"/api/v1/friendships/{VIEWER_ID}/(followers|following)/", path)
        if match:
            ids = FOLLOWERS if match.group(1) == "followers" else FOLLOWING
            query = parse_qs(url.query).get("query")
            if query:
                # unfollowUser() searches the following list to confirm the account is gone.
                ids = [i for i in ids if USERS[i] == query[0] and i not in unfollowed]
            return route.fulfill(json={"users": [raw_user(i) for i in ids], "has_more": False, "status": "ok"})
        if path == "/api/graphql" and req.method == "POST":
            body = {k: v[0] for k, v in parse_qs(req.post_data or "").items()}
            target = json.loads(body.get("variables", "{}")).get("target_user_id")
            unfollow_requests.append({"target": target, "body": body, "headers": req.headers})
            if args.broken:
                # What Instagram does for routes the web client isn't served: a 200 HTML page.
                return route.fulfill(content_type="text/html", body="<!doctype html><html><body>Instagram</body></html>")
            unfollowed.add(target)
            return route.fulfill(json={"data": {"xdt_api__v1__friendships__destroy": {"friendship_status": {"following": False}}}})
        unexpected.append(f"{req.method} {req.url}")
        return route.abort()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(locale="en-US", viewport={"width": 1400, "height": 900})
        context.add_cookies([
            {"name": "csrftoken", "value": "mockcsrf", "url": "https://www.instagram.com"},
            {"name": "ds_user_id", "value": VIEWER_ID, "url": "https://www.instagram.com"},
        ])
        context.add_init_script(f"localStorage.setItem('iu_timings', {json.dumps(json.dumps(TIMINGS))})")
        context.route("**/*", handle)
        page = context.new_page()
        page.on("console", lambda msg: msg.type == "error" and console_errors.append(msg.text))
        page.on("pageerror", lambda err: console_errors.append(str(err)))
        page.on("dialog", lambda dialog: dialog.accept())

        page.goto("https://www.instagram.com/")
        page.wait_for_selector("button.run-scan")
        page.screenshot(path=out / "1-launch.png")

        page.click("button.run-scan")
        page.wait_for_selector(".account-checkbox:not([disabled])")
        results = page.locator(".result-item .account-checkbox")
        shown = page.locator(".result-item").all_inner_texts()
        page.screenshot(path=out / "2-scan.png")

        for i in range(min(args.select, results.count())):
            results.nth(i).check()
        page.click("button.unfollow")
        page.wait_for_selector(".unfollow-log-container .clr-green")
        page.screenshot(path=out / "3-unfollow.png")
        log_text = page.inner_text(".unfollow-log-container")
        browser.close()

    summary = {
        "results_shown": [text.split()[0] for text in shown],
        "unfollow_requests": [
            {"target_user_id": r["target"], "doc_id": r["body"].get("doc_id"), "fb_dtsg": r["body"].get("fb_dtsg"), "csrf": r["headers"].get("x-csrftoken")}
            for r in unfollow_requests
        ],
        "unexpected_requests": unexpected,
        "console_errors": console_errors,
        # The log pads names with &nbsp;, which a cp1252 Windows console prints as garbage.
        "log": [" ".join(line.split()) for line in log_text.strip().splitlines()],
        "screenshots": str(out),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    logged = summary["log"]
    expected_prefix = "Failed to unfollow" if args.broken else "Unfollowed"
    ok = (
        len(shown) == len(FOLLOWING) - len(FOLLOWERS)
        and len(unfollow_requests) == args.select
        and all(r["target"] in USERS and r["body"].get("fb_dtsg") == "mockdtsg" for r in unfollow_requests)
        and sum(line.startswith(expected_prefix) for line in logged) == args.select
        and not unexpected
        and not console_errors
    )
    print("OK" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

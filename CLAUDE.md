# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Preact + TypeScript app bundled into a single script (`dist/dist.js`) that the user pastes into the DevTools console on `www.instagram.com`. It wipes the page (`document.body.innerHTML = ""`) and renders its own UI to list accounts that don't follow back, whitelist them, and unfollow in bulk. There is no backend; everything runs in the user's logged-in Instagram session.

## Commands

- `bun run build` — webpack production build to `dist/dist.js`, then `scripts/update-index.js` embeds the bundle into `public/index.html`. Always commit both files together.
- `bun run copy` — build, then copy `dist/dist.js` to the clipboard (Windows).
- `bunx tsc --noEmit` — type check. `tsconfig.json` has `noUnusedLocals`/`noUnusedParameters`, so leftover imports fail.
- `bun run build-dev` — build, then `webpack serve`.
- There are no tests and no linter configured. To run the real scan/unfollow flow headlessly against a mocked Instagram, use the `run-instagramunfollowers` skill (`.claude/skills/run-instagramunfollowers/`).

The project uses Bun (lockfile `bun.lock`), never npm. CI (`.github/workflows/build_and_deploy_pages.yaml`) runs `bun install --frozen-lockfile && bun run build` on push to `master` and deploys `public/` to GitHub Pages.

## Architecture

- **`public/index.html`** is the landing page (GitHub Pages). It holds the whole bundle as an escaped string literal between `const instagramScript = "` and `";//__END_OF_SCRIPT__`. The page offers it through a copy button and a bookmarklet. Never edit that string by hand; `update-index.js` rewrites it on every build.
- **`src/main.tsx`** holds nearly all logic in one `App` component. `State` (`src/model/state.ts`) is a discriminated union on `status`: `initial` → `scanning` → `unfollowing`. The scan and unfollow loops run as `useEffect`s keyed on `state.status`, and components receive `state`/`setState` directly. Always use `assertUnreachable` in switches over `status`.
- **Scan flow:** `fetchList` pages through Instagram's private REST endpoints `/api/v1/friendships/<ds_user_id>/following|followers/` (see `fetchFriendshipsPage` in `src/utils/utils.ts`, which needs the `X-IG-App-ID` header). It fetches the full following list first, then only follower IDs into a `Set`, to save memory. It pauses between cycles using the user's `Timings` and honors the global `scanningPaused` flag. It stops at the `*_PAGE_SAFETY_LIMIT` caps in `src/constants/constants.ts`. Progress is an estimate because these endpoints don't return totals. Partial scans are reported with a toast rather than thrown.
- **Unfollow flow:** `unfollowUser` in `src/utils/utils.ts` runs Instagram's GraphQL `usePolarisUnfollowMutation` (`INSTAGRAM_UNFOLLOW_DOC_ID`, `fb_dtsg`/`lsd` read from the page) and only reports success once Instagram confirms the follow is gone. Paced by `timeBetweenUnfollows` plus a long pause every few unfollows.
- **Persistence:** only `localStorage`, through `src/utils/whitelist-manager.ts` (whitelist plus timings; keys `iu_*` in constants).
- **Display pipeline:** `getUsersForDisplay` (tab, search and filter checkboxes) → `sortByUsername` → rendered as one scrolling list with letter separators (`Searching.tsx`).
- **Local preview:** on `localhost`/`127.0.0.1`, `isLocalPreview` skips network calls and uses fake users from `_getPreviewUsers()`. `?preview=scanning` starts directly in the results view.
- **`react` is aliased to `preact/compat`** in both `webpack.config.js` and `tsconfig.json` `paths`, so React-style imports resolve to Preact.
- **Styles** are SCSS imported from `src/styles.scss` and injected at runtime by style-loader, all scoped under the `.iu` root class.

## Repo / git

This checkout is a personal fork. `origin` = `dimapoint/InstagramUnfollowers` (push here only when asked). `upstream` = `davidarroyo1234/InstagramUnfollowers` is fetch-only. Never push to it or open PRs against it.

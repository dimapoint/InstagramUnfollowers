# Instagram Unfollowers

A high-performance, browser-injected tool for managing Instagram followers and unfollowers. It identifies accounts you follow that don't follow you back and allows for managed, automated unfollowing with safety delays.

## Project Overview

- **Purpose**: Automate the identification and unfollowing of non-followers on Instagram while respecting rate limits.
- **Main Technologies**:
  - **Framework**: Preact (aliased to React via `react: 'preact/compat'`) for minimal bundle size.
  - **Language**: TypeScript for robust type safety.
  - **Styling**: SCSS (Sass) for modular and maintainable styles.
  - **Build Tool**: Webpack 5 with `ts-loader` and `sass-loader`.
  - **Runtime**: Designed to run directly on `instagram.com` (requires user cookies like `ds_user_id` and `csrftoken`).

## Architecture

- **Entry Point**: `src/main.tsx` initializes the React/Preact application and mounts it to the document body if on the correct hostname.
- **State Management**: Uses a tagged union `State` in `src/model/state.ts` to manage application phases: `initial`, `scanning`, and `unfollowing`.
- **Components**: Functional components located in `src/components/`, including specialized views for each state and a `WhitelistManager`.
- **Utils**: `src/utils/utils.ts` contains core logic for API interactions, CSV/JSON exports, and "human-like" behavior simulation (randomized sleep cycles).
- **Styles**: Organized in `src/styles/` with a focus on UI/UX improvements and helper classes.

## Building and Running

The project uses `bun` as the preferred task runner, but `npm` should also work.

| Task | Command | Description |
| :--- | :--- | :--- |
| **Build Production** | `bun run build` | Bundles the app and updates the index file. |
| **Development Mode** | `bun run build-dev` | Serves the app in development mode with hot reloading. |
| **Production Server** | `bun run build-prod` | Serves the production build locally. |
| **Webpack Only** | `bun run webpack-build` | Runs webpack production build. |

**Output**: The build process generates `dist/dist.js`, which is the main script to be injected or used.

## Development Conventions

- **Type Safety**: Use TypeScript interfaces/types for all data models (see `src/model/`).
- **Exhaustive Checks**: Always use the `assertUnreachable` pattern in `switch` statements for finite states/types to ensure all cases are handled.
- **React Compatibility**: Write standard React code; Webpack handles the aliasing to Preact.
- **Safety First**: When modifying API interaction logic (scanning/unfollowing), always maintain or improve the "sleep" and "pause" mechanisms to prevent user account bans.
- **State Immutability**: Prefer `readonly` properties in state and model definitions to ensure predictable state transitions.
- **Styling**: Use the SCSS variables defined in `src/styles/_variables.scss` to maintain visual consistency.

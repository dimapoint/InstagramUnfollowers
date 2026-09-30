# Instagram Unfollowers

A browser script that shows who doesn't follow you back on Instagram. Nothing to install: it runs in your own logged-in session, and your data never leaves your browser.

## Usage

1. Get the script. Either use the **COPY** button on this repo's GitHub Pages site, or build it yourself (see below) and copy `dist/dist.js`.
2. Log in at [instagram.com](https://www.instagram.com) and open the developer console (`Ctrl+Shift+J` on Windows, `⌘+⌥+I` on macOS).
3. Paste the script, press Enter, then click **RUN**.
4. When the scan finishes, select the accounts you want and click **Unfollow**.

Notes:
- Results appear only once the scan is near completion, because the following and followers lists must both be loaded first.
- Click a profile picture to whitelist that account, which protects it from unfollowing. The whitelist is saved in your browser, and you can export, import or clear it from **Settings**.
- **Settings** also controls the delays between requests. Raise them if Instagram starts rate-limiting you.
- On Android, you can run it through the [Eruda browser](https://github.com/liriliri/eruda-android/releases/).

## Development

```sh
nvm use          # Node version from .nvmrc
npm install
npm run build    # outputs dist/dist.js and embeds it in public/index.html
```

## Disclaimer

Not affiliated with, endorsed by, or connected to Instagram. Use at your own risk.

Licensed under the [MIT License](LICENSE).

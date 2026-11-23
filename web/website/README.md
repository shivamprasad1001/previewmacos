# Preview (macOS Edition) Website

Static marketing and download website for [Preview (macOS Edition)](https://github.com/shivamprasad1001/previewmacos).
Built with plain HTML, CSS, and vanilla JavaScript - no framework and no build step required.

## Contents

- `index.html` - Single-page semantic HTML document
- `style.css` - Responsive light and dark theme styles (`prefers-color-scheme` + `localStorage`)
- `script.js` - OS download detection, GitHub Releases API sync (with `v1.7.2` fallback), clipboard copy, gallery lightbox, shortcut filter, and scroll reveal
- `assets/` - Official app icon and screenshots downloaded from the repository
- `sitemap.xml` & `robots.txt` - Search indexing metadata

## Local Preview

Serve the `/website` directory with any static HTTP server:

```bash
cd website
python3 -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

## Deploy to GitHub Pages

### Option A: Deploy from `/website` via GitHub Actions

Create `.github/workflows/pages.yml` in the repository root:

```yaml
name: Deploy Website to GitHub Pages
on:
  push:
    branches: [main]
    paths: ["website/**"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: website
      - id: deployment
        uses: actions/deploy-pages@v4
```

Then enable **Settings -> Pages -> Source: GitHub Actions** in your repository.

### Option B: Deploy from a `gh-pages` branch

Push only the contents of `website/` to the `gh-pages` branch (for example using `git subtree push --prefix website origin gh-pages`) and set GitHub Pages to serve from the `gh-pages` branch root.

## Pointing a `trivilabs.in` Subdomain at GitHub Pages

Example subdomain: `preview.trivilabs.in`.

1. **Add a `CNAME` file** inside `/website/CNAME` containing only your subdomain:
   ```
   preview.trivilabs.in
   ```
2. **Configure DNS** at your `trivilabs.in` DNS provider (e.g., Cloudflare or registrar DNS):
   - Record type: `CNAME`
   - Name / Host: `preview` (or your chosen subdomain)
   - Target / Value: `shivamprasad1001.github.io`
   - Proxy status: DNS only (recommended until HTTPS certificate provisioning completes)
3. **Configure Custom Domain in GitHub**:
   - Open repository **Settings -> Pages -> Custom domain**.
   - Enter `preview.trivilabs.in` and click **Save**.
   - Wait for DNS verification, then check **Enforce HTTPS**.
4. **Update canonical URLs** in `index.html`, `sitemap.xml`, and `robots.txt` if you choose a subdomain name other than `preview.trivilabs.in`.

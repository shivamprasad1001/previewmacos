# Preview (macOS Edition) - Website

This directory contains the production-ready static marketing and download website for **Preview (macOS Edition)**.

Built with plain semantic HTML5, modern vanilla CSS, and lightweight JavaScript. No build step, bundler, or external framework required.

---

## Directory Structure

```text
website/
├── index.html       # Single-page semantic HTML5 layout (11 sections)
├── style.css        # Apple-inspired design system with light/dark theme
├── script.js        # GitHub Releases API, OS detection, lightbox, filters
├── robots.txt       # Search engine crawler directives
├── sitemap.xml      # XML sitemap for SEO indexation
├── README.md        # Deployment and hosting instructions
└── assets/          # High-resolution local images and icons
    ├── icon.png
    ├── preview_main_dark.png
    ├── preview_main_light.png
    ├── preview_markup_showcase.png
    ├── preview_adjust_color.png
    └── preview_updater.png
```

---

## Local Development & Testing

Serve the `website/` directory using Python's built-in HTTP server:

```bash
# From the repository root
python3 -m http.server 8080 --directory website
```

Open your browser to `http://localhost:8080` to preview the site.

---

## Deployment Options

### Option 1: GitHub Pages (Recommended)

You can publish the site directly via GitHub Pages using either GitHub Actions or the `gh-pages` branch.

#### Method A: Dedicated `gh-pages` Branch
1. Create and switch to an orphan branch or push the `website` directory subtree:
   ```bash
   git subtree push --prefix website origin gh-pages
   ```
2. Navigate to your repository on GitHub:
   - Go to **Settings** > **Pages**.
   - Under **Build and deployment** > **Source**, choose **Deploy from a branch**.
   - Select `gh-pages` as the branch and `/ (root)` as the folder.
   - Click **Save**.

#### Method B: GitHub Actions Workflow
Create `.github/workflows/deploy-pages.yml`:
```yaml
name: Deploy Website to GitHub Pages

on:
  push:
    branches: [ main ]
    paths:
      - 'website/**'

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: 'pages'
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: 'website/'

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

### Option 2: Custom Subdomain Setup (`preview.trivilabs.in`)

To connect the site to `preview.trivilabs.in`:

1. **Add CNAME File**:
   Create a file named `CNAME` inside the `website/` folder (or configure it in repository settings):
   ```text
   preview.trivilabs.in
   ```

2. **Configure DNS Records** (at your DNS provider for `trivilabs.in`):
   - **Type**: `CNAME`
   - **Name / Host**: `preview`
   - **Target / Value**: `shivamprasad1001.github.io` (or your GitHub username `.github.io`)
   - **TTL**: Automatic or 3600

3. **Configure Custom Domain in GitHub**:
   - In your repo, go to **Settings** > **Pages**.
   - Under **Custom domain**, enter `preview.trivilabs.in`.
   - Click **Save**.
   - Wait for DNS check to succeed, then check **Enforce HTTPS**.

---

## Quality & Optimization Notes

- **Zero Hotlinks**: All screenshots and icons are served locally from `assets/`.
- **Theme Support**: Light and dark mode support with automatic `prefers-color-scheme` detection and local storage persistence.
- **Dynamic Releases**: Automatically fetches the latest `.deb` and `.exe` binaries from the GitHub Releases API with robust fallback to `v1.7.0`.
- **Accessibility & Performance**: Built to adhere to WCAG AA color contrast standards, explicit image aspect ratios to prevent Cumulative Layout Shift (CLS), and keyboard navigable controls.

# Preview (macOS Edition) - Web & GitHub Pages

This directory contains the web assets, build configuration, and automated deployment setup for the **Preview (macOS Edition)** static website.

## Prerequisites

- Node.js (v18+)
- npm (v9+)

## Scripts

- `npm install` - Install dependencies
- `npm run dev` - Start local development server on `http://localhost:3000`
- `npm run build` - Build the production-ready static site into `dist/` (configured with relative paths and `.nojekyll` for GitHub Pages)
- `npm test` - Run website integrity test suite
- `npm run lint` - Run TypeScript check
- `npm run deploy` - Build and publish directly to the `gh-pages` branch on GitHub

---

## Deploying to GitHub Pages

### Option 1: Automatic via GitHub Actions (Recommended)
An automated workflow is configured at [`.github/workflows/deploy-pages.yml`](../.github/workflows/deploy-pages.yml).

1. In your GitHub repository, open **Settings** > **Pages**.
2. Under **Build and deployment** > **Source**, choose **GitHub Actions**.
3. Push commits to `main` (specifically changes in `web/` or `website/`), and GitHub will automatically run tests, build the website, and publish it to GitHub Pages.

### Option 2: CLI Deploy via `gh-pages` Branch
If you prefer deploying from a branch:
1. Run:
   ```bash
   npm run deploy
   ```
2. In your GitHub repository, navigate to **Settings** > **Pages**.
3. Under **Build and deployment** > **Source**, choose **Deploy from a branch**.
4. Select `gh-pages` branch and `/ (root)` folder.
5. Click **Save**.

# TW Strategy Lab site

Static landing page for the quant-platform project. No build step: `index.html` and `reports/` are served as-is.

- `reports/` contains simulated-data sample reports only. Do not add real market prices here (data-provider terms usually forbid redistribution).
- Deploys to GitHub Pages from `main` via `.github/workflows/pages.yml`.
- Enable Pages in repo settings with source "GitHub Actions" before the first deploy.

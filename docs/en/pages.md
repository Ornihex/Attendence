# Deploy Docs to GitHub Pages

## Stack
- `MkDocs`
- `Material for MkDocs`
- GitHub Actions (`.github/workflows/docs-pages.yml`)

## Local preview
Install docs dependencies:
```bash
pip install mkdocs mkdocs-material
```

Run docs server:
```bash
mkdocs serve
```

Open: `http://127.0.0.1:8000`

## Static build
```bash
mkdocs build
```
Build output: `site/`.

## GitHub Actions deployment
1. Open repository `Settings -> Pages`.
2. In `Build and deployment`, choose `Source: GitHub Actions`.
3. Push changes to your default branch.
4. Workflow builds and deploys docs automatically.

## Required customization
Before first deploy, update these fields in `mkdocs.yml`:
- `site_url`
- `repo_url`
- `repo_name`

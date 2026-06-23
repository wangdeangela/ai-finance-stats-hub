# GitHub Actions CI (optional)

If your PAT lacks the `workflow` scope, `git push` cannot upload files under `.github/workflows/`.

## Option 1: Re-enable CI (recommended)

1. Open GitHub -> **Settings** -> **Developer settings** -> **Personal access tokens**
2. Edit or create a token and enable the **`workflow`** scope
3. Update local credentials, then run:

```bash
mkdir -p .github/workflows
cp docs/ci.yml.example .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "Add GitHub Actions CI workflow"
git push
```

## Option 2: Skip CI for now

You can still run `pytest tests/` and `python main.py --demo` locally; Streamlit deployment is unaffected.

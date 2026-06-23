# GitHub Actions CI（可选）

当前 PAT 若无 `workflow` 权限，无法通过 `git push` 上传 `.github/workflows/` 下的文件。

## 方式一：恢复 CI（推荐）

1. 打开 GitHub → **Settings** → **Developer settings** → **Personal access tokens**
2. 编辑或新建 Token，勾选 **`workflow`** 权限
3. 更新本机凭据后执行：

```bash
mkdir -p .github/workflows
cp docs/ci.yml.example .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "Add GitHub Actions CI workflow"
git push
```

## 方式二：暂不启用 CI

项目仍可在本地运行 `pytest tests/` 与 `python main.py --demo`，不影响 Streamlit 部署。

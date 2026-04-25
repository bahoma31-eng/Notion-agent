# تعليمات Copilot لهذا المستودع

## GitHub Actions Workflows

- **دائماً** استخدم `--auto` وليس `--admin` عند دمج الـ PR تلقائياً
- **دائماً** أضف `permissions: contents: write` و `pull-requests: write` لكل workflow ينشئ PR
- **دائماً** استخدم `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` وليس PAT خاصاً
- للتفاصيل راجع `.github/WORKFLOW_GUIDE.md`

## النمط الصحيح لـ merge

```bash
# ✅ صحيح
gh pr merge "$PR_NUMBER" --squash --auto --delete-branch

# ❌ ممنوع
gh pr merge "$PR_NUMBER" --squash --admin --delete-branch
```

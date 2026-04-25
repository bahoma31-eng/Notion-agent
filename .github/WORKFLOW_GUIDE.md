# دليل كتابة GitHub Actions Workflows

> **اقرأ هذا قبل كتابة أي workflow جديد**

---

## ✅ القاعدة الذهبية للـ PR الآلي

عند إنشاء PR وإغلاقه تلقائياً، **دائماً استخدم `--auto`** وليس `--admin`.

```yaml
# ✅ صحيح
gh pr merge "$PR_NUMBER" --squash --auto --delete-branch

# ❌ خطأ — يفشل مع Branch Protection
gh pr merge "$PR_NUMBER" --squash --admin --delete-branch
```

---

## ✅ الـ Permissions الإلزامية

كل workflow ينشئ PR يجب أن يحتوي على:

```yaml
permissions:
  contents: write
  pull-requests: write
```

---

## ✅ Template كامل للـ PR الآلي

```yaml
name: My Automated Workflow

on:
  schedule:
    - cron: "0 7 * * 0"  # كل أحد 07:00 UTC
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  my_job:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      # ... خطواتك هنا ...

      - name: Commit and open PR
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}
        run: |
          set -euo pipefail

          if ! git status --porcelain | grep -q .; then
            echo "No changes to commit."
            exit 0
          fi

          DATE=$(date +%Y-%m-%d)
          BRANCH="auto/my-task-${DATE}"

          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git push origin --delete "$BRANCH" 2>/dev/null || true
          git checkout -b "$BRANCH"
          git add .
          git commit -m "Auto: my task for ${DATE}"
          git push origin "$BRANCH"

          EXISTING_PR=$(gh pr list --head "$BRANCH" --json number --jq '.[0].number' 2>/dev/null || echo "")

          if [ -n "$EXISTING_PR" ]; then
            PR_NUMBER="$EXISTING_PR"
          else
            PR_URL=$(gh pr create \
              --title "Auto task: ${DATE}" \
              --body "Automated PR created on ${DATE}." \
              --base "${DEFAULT_BRANCH:-main}" \
              --head "$BRANCH")
            PR_NUMBER=$(echo "$PR_URL" | grep -o '[0-9]*$')
          fi

          gh pr merge "$PR_NUMBER" --squash --auto --delete-branch
          echo "Done."
```

---

## ✅ إعدادات Branch Ruleset (مُعدَّة مسبقاً)

المستودع مُهيَّأ بـ Ruleset على `main` يتضمن:
- Bypass: **Repository admin** ✅
- Required approvals: **0** ✅
- Require PR before merging: **مفعّل** ✅

هذا يعني `--auto` سيعمل دائماً بلا أي تدخل يدوي.

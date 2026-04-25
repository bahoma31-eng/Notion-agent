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

---

## 🔐 قاعدة GITHUB_TOKEN — إلزامية لكل Issue

### ما هو `secrets.GITHUB_TOKEN`؟

`secrets.GITHUB_TOKEN` هو **توكن داخلي تلقائي** يُوفّره GitHub في كل Workflow run بدون أي إنشاء أو إضافة يدوية.

> ⚠️ لا تطلب من المستخدم إنشاءه كـ Secret يدوي — GitHub يرفض أي Secret يبدأ بـ `GITHUB_`

### الاستخدام الصحيح في الـ Workflow

```yaml
permissions:
  contents: write
  pull-requests: write

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: تشغيل السكريبت
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # ✅ تلقائي — لا يُنشأ يدوياً
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python scripts/my_script.py
```

### الاستخدام الصحيح في Python

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GH_TOKEN"],  # يأتي من secrets.GITHUB_TOKEN تلقائياً
)
```

---

## 📋 المتغيرات السرية المخزنة في المستودع (Repository Secrets)

المستودع يحتوي على الـ Secrets التالية في `Settings → Secrets and variables → Actions`:

| اسم الـ Secret | الوصف | طريقة التوفير |
|----------------|-------|--------------|
| `GH_TOKEN` | يُعيَّن من `${{ secrets.GITHUB_TOKEN }}` | ✅ تلقائي — **لا يُنشأ يدوياً أبداً** |
| `FACEBOOK_APP_ID` | معرّف تطبيق فيسبوك من Meta Developers | ⚙️ يدوي |
| `FACEBOOK_APP_SECRET` | المفتاح السري لتطبيق فيسبوك | ⚙️ يدوي |
| `FB_PAGE_ACCESS_TOKEN` | توكن الوصول لصفحة فيسبوك | ⚙️ يدوي |
| `FB_PAGE_ID` | معرّف صفحة فيسبوك | ⚙️ يدوي |
| `SMTP_PASSWORD` | كلمة مرور البريد الإلكتروني (SMTP) | ⚙️ يدوي |
| `SMTP_USER` | اسم المستخدم للبريد الإلكتروني (SMTP) | ⚙️ يدوي |

### قواعد الاستخدام في كل Issue

- عند كتابة أي Issue يحتاج متغيرات سرية، **استخدم الأسماء المذكورة أعلاه مباشرةً**
- **لا تقترح إنشاء Secrets جديدة** إذا كان المطلوب موجوداً بالفعل في الجدول
- `GH_TOKEN` لا يُطلب من المستخدم إنشاؤه أبداً — هو تلقائي
- إذا احتاج النظام الجديد Secret غير موجود في الجدول، **أذكره صراحةً** في الـ Issue

---

## 🤖 نماذج الذكاء الاصطناعي المسموح بها

كل سكريبت أو أداة يتم بناؤها في هذا المستودع يجب أن:

- ✅ تستخدم **GitHub Models حصراً** عبر:
  - Base URL: `https://models.inference.ai.azure.com`
  - Token: `GH_TOKEN` (من `secrets.GITHUB_TOKEN` — تلقائي)
- ❌ لا تستخدم أي نموذج خارجي مثل:
  - OpenAI API المباشر (`api.openai.com`)
  - Google Gemini
  - Anthropic Claude
  - أي مفتاح API خارجي آخر

### مثال الاتصال الصحيح

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GH_TOKEN"],
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=500,
)
```

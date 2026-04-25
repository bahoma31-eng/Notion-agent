# تعليمات Copilot لهذا المستودع

## GitHub Actions Workflows

- **دائماً** استخدم `--auto` وليس `--admin` عند دمج الـ PR تلقائياً
- **دائماً** أضف `permissions: contents: write` و `pull-requests: write` لكل workflow ينشئ PR
- **دائماً** استخدم `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` لعمليات المستودع (فتح PR، push، merge)
- **دائماً** استخدم `MODELS_TOKEN` للاتصال بـ GitHub Models API حصراً
- **لا تضع كلاهما في نفس المتغير** — لكل استخدام متغيره المخصص
- للتفاصيل راجع `.github/WORKFLOW_GUIDE.md`

## النمط الصحيح لـ merge

```bash
# ✅ صحيح
gh pr merge "$PR_NUMBER" --squash --auto --delete-branch

# ❌ ممنوع
gh pr merge "$PR_NUMBER" --squash --admin --delete-branch
```

---

## ⚠️ دروس مستفادة من تجارب سابقة

### درس 1: `GITHUB_TOKEN` لا يعمل مع GitHub Models API

`secrets.GITHUB_TOKEN` التلقائي **لا يحمل صلاحية `models`** ويعطي خطأ 401.

```
❌ خطأ: api_key=os.environ["GH_TOKEN"]  # مع GH_TOKEN = secrets.GITHUB_TOKEN
✅ صحيح: api_key=os.environ["MODELS_TOKEN"]  # PAT مخصص بصلاحية models
```

> استخدم `MODELS_TOKEN` حصراً للاتصال بـ GitHub Models.
> استخدم `GITHUB_TOKEN` حصراً لعمليات المستودع (PR, push, merge).

---

### درس 2: Push مباشر على `main` محظور

المستودع يحتوي على Ruleset يمنع أي push مباشر على `main`.

```yaml
# ❌ ممنوع
git push origin main

# ✅ النمط الصحيح: branch جديد → PR → merge --auto
BRANCH="logs/post-$(date +'%Y%m%d-%H%M%S')"
git checkout -b "$BRANCH"
git push origin "$BRANCH"
gh pr create --base main --head "$BRANCH" ...
gh pr merge "$PR_NUMBER" --squash --auto --delete-branch
```

---

### درس 3: التحقق من حالة الـ PR قبل إعادة التشغيل

إذا أنشأ Copilot ـ PR للإصلاح، لا تعيد تشغيل الـ Workflow قبل دمجه.

```
❌ خطأ: إعادة التشغيل والـ PR لا يزال Draft/Open
✅ صحيح: تحويل الـ PR من Draft → Ready → دمجه → ثم إعادة التشغيل
```

---

## 🤖 قاعدة تكليف Copilot — إلزامية بعد كل Issue

> ⚠️ بعد إنشاء أي Issue والحصول على موافقة المستخدم،
> **يجب تكليف GitHub Copilot بالتنفيذ تلقائياً** بدون انتظار أي خطوة يدوية.

```
1. إنشاء Issue  →  موافقة المستخدم  →  تكليف Copilot تلقائياً
                                      ↓
                           استدعاء assign_copilot_to_issue فوراً
```

---

## 🔐 قاعدة GITHUB_TOKEN — إلزامية لكل Issue

`secrets.GITHUB_TOKEN` هو **توكن داخلي تلقائي** يُوفّره GitHub في كل Workflow run.

> ⚠️ لا تطلب من المستخدم إنشاءه — GitHub يرفض أي Secret يبدأ بـ `GITHUB_`

```yaml
# ✅ لعمليات المستودع
permissions:
  contents: write
  pull-requests: write
env:
  GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# ✅ لـ GitHub Models حصراً
env:
  MODELS_TOKEN: ${{ secrets.MODELS_TOKEN }}
```

---

## 📋 المتغيرات السرية المخزنة في المستودع

| اسم الـ Secret | الوصف | طريقة التوفير |
|----------------|-------|--------------|
| `GH_TOKEN` | يُعيَّن من `${{ secrets.GITHUB_TOKEN }}` — لعمليات المستودع | ✅ تلقائي |
| `MODELS_TOKEN` | PAT بصلاحية `models` — **لـ GitHub Models حصراً** | ⚠️ يدوي |
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
- إذا احتاج النظام Secret غير موجود في الجدول، **أذكره صراحةً** في الـ Issue

---

## 🤖 نماذج الذكاء الاصطناعي المسموح بها

- ✅ تستخدم **GitHub Models حصراً** عبر:
  - Base URL: `https://models.inference.ai.azure.com`
  - Token: `MODELS_TOKEN` (من `secrets.MODELS_TOKEN` — PAT يدوي)
- ❌ لا تستخدم أي نموذج خارجي مثل OpenAI API أو Gemini أو Claude

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["MODELS_TOKEN"],  # ✅ PAT بصلاحية models
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=500,
)
```

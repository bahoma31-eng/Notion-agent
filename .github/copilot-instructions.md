# تعليمات Copilot لهذا المستودع

## GitHub Actions Workflows

- **دائماً** استخدم `--auto` وليس `--admin` عند دمج الـ PR تلقائياً
- **دائماً** أضف `permissions: contents: write` و `pull-requests: write` لكل workflow ينشئ PR
- **دائماً** استخدم `REPO_TOKEN` لعمليات المستودع التي تحتاج فتح PR ودمجه (push، merge، pr create)
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
> استخدم `REPO_TOKEN` حصراً لعمليات المستودع (PR, push, merge).

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

### درس 4: `GITHUB_TOKEN` التلقائي لا يكفي لدمج PRs مع Rulesets

`secrets.GITHUB_TOKEN` التلقائي **لا يملك صلاحية كافية** لفتح PR ودمجه عندما تكون Rulesets مُفعّلة على `main`.

```yaml
# ❌ يفشل في Step 6 مع Rulesets
GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# ✅ الصحيح: استخدام REPO_TOKEN (PAT بصلاحية repo كاملة)
GH_TOKEN: ${{ secrets.REPO_TOKEN }}
```

> استخدم `REPO_TOKEN` في أي Step يحتاج فتح PR أو دمجه.

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

## 🔐 قاعدة Tokens — إلزامية لكل Issue

| التوكن | الاستخدام | المصدر |
|--------|-----------|--------|
| `secrets.GITHUB_TOKEN` | توكن تلقائي داخلي — **لا يُستخدم لعمليات PR/merge مع Rulesets** | ✅ تلقائي |
| `secrets.REPO_TOKEN` | عمليات المستودع: PR، push، merge — **الأولوية على GITHUB_TOKEN** | ⚠️ PAT يدوي بصلاحية `repo` |
| `secrets.MODELS_TOKEN` | GitHub Models API حصراً | ⚠️ PAT يدوي بصلاحية `models` |

```yaml
# ✅ النمط الصحيح لكل workflow يفتح PR ويدمجه
permissions:
  contents: write
  pull-requests: write

steps:
  - name: Run script (GitHub Models)
    env:
      GH_TOKEN: ${{ secrets.MODELS_TOKEN }}   # للنماذج فقط

  - name: Commit and push log via PR branch
    env:
      GH_TOKEN: ${{ secrets.REPO_TOKEN }}     # لعمليات المستودع
```

> ⚠️ لا تطلب من المستخدم إنشاء `GITHUB_TOKEN` — GitHub يرفع خطأ لأي Secret يبدأ بـ `GITHUB_`

---

## 📋 المتغيرات السرية المخزنة في المستودع

| اسم الـ Secret | الوصف | طريقة التوفير |
|----------------|-------|--------------| 
| `REPO_TOKEN` | PAT بصلاحية `repo` كاملة — لعمليات PR/push/merge | ⚠️ يدوي |
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
- `REPO_TOKEN` هو التوكن الأساسي لكل عمليات المستودع — **استخدمه بدلاً من GITHUB_TOKEN**
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

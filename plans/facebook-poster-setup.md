# دليل إعداد نظام النشر التلقائي على فيسبوك — مطعم الركن الجميل

## 📋 نظرة عامة

هذا النظام ينشر تلقائياً محتوى ترويجياً على صفحة فيسبوك مطعم **"الركن الجميل"** كل ساعة، باستخدام:
- **OpenAI API (GPT-4o)** لتوليد منشورات إبداعية بالعربية والدارجة الوهرانية
- **Facebook Graph API** لنشر المحتوى على الصفحة

---

## 🔐 1. الحصول على `FB_PAGE_ACCESS_TOKEN`

### الخطوات:

1. انتقل إلى [Meta for Developers](https://developers.facebook.com/)
2. أنشئ تطبيقاً جديداً أو افتح تطبيقاً موجوداً
3. أضف منتج **Facebook Login** أو **Pages API** للتطبيق
4. انتقل إلى **Graph API Explorer**: [https://developers.facebook.com/tools/explorer/](https://developers.facebook.com/tools/explorer/)
5. اختر تطبيقك من القائمة المنسدلة
6. انقر على **"Generate Access Token"** واختر صفحتك
7. اختر الصلاحيات التالية على الأقل:
   - `pages_manage_posts`
   - `pages_read_engagement`
8. انسخ الـ **Page Access Token** الناتج

> ⚠️ **ملاحظة**: الـ Token المولَّد من Explorer يصلح للاختبار فقط (صالح لساعتين).  
> للنشر التلقائي المستمر، احصل على **Long-Lived Page Access Token** باتباع [هذا الدليل](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived/).

---

## 🔑 2. إضافة الـ Secrets على GitHub

انتقل إلى:  
`Settings → Secrets and variables → Actions → New repository secret`

أضف الـ Secrets الثلاثة التالية:

| اسم الـ Secret | القيمة |
|----------------|--------|
| `OPENAI_API_KEY` | مفتاح OpenAI API من [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `FB_PAGE_ID` | معرّف صفحة فيسبوك (يمكن إيجاده في إعدادات الصفحة → About → Page ID) |
| `FB_PAGE_ACCESS_TOKEN` | الـ Token الذي حصلت عليه في الخطوة السابقة |

---

## ▶️ 3. تشغيل الـ Workflow يدوياً للاختبار

1. انتقل إلى تبويب **Actions** في المستودع
2. اختر **"🍕 Facebook Auto Post — الركن الجميل"** من القائمة الجانبية
3. انقر على **"Run workflow"** ← **"Run workflow"**
4. راقب السجلات للتأكد من نجاح النشر

---

## ⏰ 4. تغيير تكرار النشر (cron)

افتح ملف `.github/workflows/facebook-auto-post.yml` وعدّل قيمة `cron`:

```yaml
on:
  schedule:
    - cron: '0 * * * *'   # الإعداد الحالي: كل ساعة
```

### أمثلة على قيم cron شائعة:

| القيمة | التكرار |
|--------|---------|
| `'0 * * * *'` | كل ساعة |
| `'0 */2 * * *'` | كل ساعتين |
| `'0 9,13,18 * * *'` | 3 مرات يومياً (9ص، 1م، 6م) UTC |
| `'0 8 * * *'` | مرة يومياً الساعة 8 صباحاً UTC |
| `'0 8 * * 1,3,5'` | ثلاثة أيام أسبوعياً (الاثنين، الأربعاء، الجمعة) |

> 💡 يمكنك استخدام [crontab.guru](https://crontab.guru/) لفهم وكتابة قيم cron.

---

## 🗂️ هيكل الملفات

```
scripts/
└── facebook_poster.py          # السكريبت الرئيسي للنشر

.github/
└── workflows/
    └── facebook-auto-post.yml  # GitHub Actions Workflow (يعمل كل ساعة)

requirements.txt                # مكتبات Python المطلوبة
plans/
└── facebook-poster-setup.md   # هذا الملف
```

---

## 🛠️ استكشاف الأخطاء

| الخطأ | الحل المحتمل |
|-------|-------------|
| `OPENAI_API_KEY غير موجود` | تأكد من إضافة الـ Secret بالاسم الصحيح |
| `FB_PAGE_ID أو FB_PAGE_ACCESS_TOKEN غير موجود` | تحقق من إضافة كلا الـ Secrets |
| `HTTP 190` من فيسبوك | الـ Token منتهي الصلاحية، جدّده |
| `HTTP 200` (خطأ في الأذونات) | تأكد من أن الـ Token يملك صلاحية `pages_manage_posts` |

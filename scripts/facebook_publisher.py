#!/usr/bin/env python3
"""
نظام النشر التلقائي على فيسبوك — مطعم Boncoin مرافل وهران
يولّد محتوى تسويقياً عبر GitHub Models وينشره على صفحة فيسبوك.
الإصدار 2.0 — مع خطة تنفيذية 12 أسبوعاً وتوليد ذكي حسب الوقت واليوم.
"""

import os
import csv
import datetime
import smtplib
from email.mime.text import MIMEText

import requests
from openai import OpenAI

# عنوان استلام إشعارات البريد
NOTIFICATION_EMAIL = "bahoma31@gmail.com"

# ─── تاريخ انطلاق الخطة التسويقية ───────────────────────────────────────
# ✅ غيّر هذا التاريخ لتاريخ الإطلاق الفعلي لصفحة Boncoin
PLAN_START_DATE = datetime.datetime(2026, 5, 1)

# ─── خريطة أيام الأسبوع بالعربية ────────────────────────────────────────
DAYS_AR = {
    0: "الاثنين",
    1: "الثلاثاء",
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد",
}

# ─── دوال حساب موقع الأسبوع والشهر من الخطة ─────────────────────────────

def get_week_number(now: datetime.datetime) -> int:
    """يحسب رقم الأسبوع الحالي من الخطة (1 إلى 12)."""
    days_elapsed = (now - PLAN_START_DATE).days
    week = (days_elapsed // 7) + 1
    return max(1, min(week, 12))


def get_month_number(week: int) -> int:
    """يحول رقم الأسبوع إلى رقم الشهر من الخطة (1، 2، أو 3)."""
    if week <= 4:
        return 1
    elif week <= 8:
        return 2
    return 3


def build_user_message(now: datetime.datetime) -> str:
    """يبني رسالة المستخدم بالمتغيرات الديناميكية لكل استدعاء."""
    week_num  = get_week_number(now)
    month_num = get_month_number(week_num)
    day_ar    = DAYS_AR[now.weekday()]
    return (
        f"current_hour: {now.hour}\n"
        f"current_day: {day_ar}\n"
        f"week_number: {week_num}\n"
        f"month_number: {month_num}"
    )


# ─── الـ System Prompt الشامل لـ Boncoin ────────────────────────────────

SYSTEM_PROMPT = """أنت مسؤول النشر الرسمي لصفحة فيسبوك لمطعم **Boncoin** للوجبات السريعة الكائن في **مرافل، وهران، الجزائر**.

مهمتك الوحيدة: توليد منشور فيسبوك واحد جاهز للنشر الفوري، بناءً على:
- الساعة الحالية (المُمررة إليك)
- اليوم من الأسبوع (المُمرر إليك)
- رقم الأسبوع من الخطة (المُمرر إليك: week_number من 1 إلى 12)
- رقم الشهر من الخطة (المُمرر إليك: month_number من 1 إلى 3)

---

## الخطة التنفيذية للثلاثة أشهر

### الشهر الأول (الأسابيع 1-4): التأسيس والوعي بالعلامة
الهدف: تعريف الجمهور بـ Boncoin، بناء الشخصية، وخلق الانطباع الأول.
نبرة الصفحة: حماسية، دافئة، محلية، فيها روح وهرانية.
أنواع المنشورات المسموحة هذا الشهر:
- تعريف بالمطعم وموقعه في مرافل وهران
- صور الأطباق الرئيسية مع وصف شهي ومثير
- وراء الكواليس: تحضير الطعام، الطاقم، المطبخ
- قصة الاسم "Boncoin" وماذا يعني (الزاوية الجيدة)
- عروض الافتتاح والخصومات الحصرية
- دعوة الزيارة الأولى مع تحديد الموقع
- أسئلة تفاعلية بسيطة ("ما وجبتك المفضلة؟")

### الشهر الثاني (الأسابيع 5-8): بناء المجتمع والتفاعل
الهدف: تحويل المتابعين إلى زبائن دائمين، بناء عادة التفاعل.
نبرة الصفحة: ودية، مجتمعية، تشعر أن Boncoin هو مطعمهم.
أنواع المنشورات المسموحة هذا الشهر:
- مشاركة آراء الزبائن (testimonials حقيقية)
- مسابقات: "شارك صورتك واربح وجبة مجانية"
- منشور "وجبة الأسبوع" مع وصف تفصيلي ومغري
- محتوى تعليمي خفيف ("لماذا اخترنا هذا الخبز؟")
- استطلاعات رأي ("أيهما تفضل: البرجر أم الشاورما؟")
- تسليط الضوء على فريق العمل
- إعلان برنامج الولاء (بطاقة 10 وجبات = وجبة مجانية)

### الشهر الثالث (الأسابيع 9-12): الترسيخ والتوسع
الهدف: ترسيخ Boncoin كمرجع الوجبات السريعة في مرافل، تشجيع الإحالات.
نبرة الصفحة: واثقة، راسخة، تعكس النجاح المتراكم.
أنواع المنشورات المسموحة هذا الشهر:
- إحصاءات ممتعة ("خدمنا 500 زبون هذا الشهر!")
- إطلاق منتج أو وجبة جديدة
- "أفضل ما قاله زبائننا" (أفضل تقييم الأسبوع)
- محتوى موسمي ومحلي (أعياد، مناسبات وهرانية)
- دعوة لإحضار الأصدقاء (Refer a Friend)
- خلف الكواليس المتقدم: مصادر المكونات، الجودة
- إعلان عروض الشهر القادم

---

## جدول أنواع المنشورات حسب الساعة

الساعة 05:00-07:59 (فجر/صباح مبكر): منشور تحفيزي، صباح الخير، تذكير بوجبة الإفطار
الساعة 08:00-10:59 (إفطار): عرض وجبة الصباح أو البرنش، دعوة للزيارة
الساعة 11:00-12:59 (منتصف النهار): إعلان وجبة الغداء اليوم، عرض الساعة، صورة شهية
الساعة 13:00-14:59 (غداء ذروة): محتوى شهي بصري قوي، عرض فوري، لا تفوت
الساعة 15:00-16:59 (فترة راحة): محتوى تفاعلي: سؤال، استطلاع، مسابقة
الساعة 17:00-18:59 (مساء مبكر): تذكير بالعشاء، عروض المساء، وراء الكواليس
الساعة 19:00-21:59 (عشاء ذروة): أقوى محتوى اليوم — صورة احترافية مع CTA قوي
الساعة 22:00-23:59 (ليل): محتوى خفيف وطريف، "أكلة الليل"، ليلة ممتازة
الساعة 00:00-04:59 (منتصف الليل): محتوى لطيف للسهرات والليالي الوهرانية

---

## تنويع المحتوى حسب اليوم

الاثنين: بداية الأسبوع — تحفيزي، عروض الأسبوع، "أسبوع جديد وجبة جديدة"
الثلاثاء: تركيز على منتج واحد بالتفصيل
الأربعاء: محتوى وراء الكواليس أو تعليمي
الخميس: تفاعلي — سؤال، استطلاع، مسابقة
الجمعة: جمعة مباركة مع عرض خاص عطلة نهاية الأسبوع
السبت: محتوى عائلي، أجواء مرافل، دعوة للعائلات
الأحد: "احكيلنا رأيك"، testimonials، استعداد للأسبوع الجديد

---

## قواعد كتابة المنشور

1. اللغة: العربية الدارجة الجزائرية بنكهة وهرانية — محلية وطبيعية، وليست فصحى رسمية.
2. الطول: بين 3 و7 أسطر فقط — لا أقل ولا أكثر.
3. الإيموجي: استخدم 2 إلى 5 إيموجي موزعة بذكاء.
4. CTA: كل منشور ينتهي بواحد من:
   سؤال للتعليق / دعوة للزيارة / طلب التاغ لصديق / دعوة للتفاعل
5. الهاشتاقات: أضف في آخر المنشور من 3 إلى 6 هاشتاقات:
   #Boncoin #مرافل_وهران #وجبات_سريعة_وهران #وهران #الجزائر
6. لا تكرر نفس فكرة المنشور السابق — كل منشور له شخصية مختلفة.
7. لا إعلانات مباشرة مملة.

---

## المدخلات التي تصلك في كل استدعاء (user message)

current_hour: [رقم من 0 إلى 23]
current_day: [الاثنين/الثلاثاء/الأربعاء/الخميس/الجمعة/السبت/الأحد]
week_number: [رقم من 1 إلى 12]
month_number: [رقم من 1 إلى 3]

---

## المخرج المطلوب منك

أخرج فقط نص المنشور الجاهز للنشر — لا شرح، لا مقدمة، لا تعليق.
فقط المنشور كما سيظهر على فيسبوك، جاهز للصق والنشر مباشرة.

---

## ممنوع تماماً

- لا تكتب بالفصحى الرسمية الجافة
- لا تكتب أكثر من 7 أسطر
- لا تضع أكثر من 6 هاشتاقات
- لا تكرر نفس الفكرة مرتين متتاليتين
- لا تضع مقدمة أو شرحاً قبل المنشور
- لا تكتب "إليك المنشور:" أو أي عبارة تمهيدية"""


# ─── توليد المنشور عبر GitHub Models ────────────────────────────────────

def generate_post() -> str:
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=os.environ["GH_TOKEN"],
    )
    now = datetime.datetime.now()
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_message(now)},
            ],
            max_tokens=350,
            temperature=0.88,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        raise RuntimeError(f"❌ فشل توليد المحتوى عبر GitHub Models: {exc}") from exc


# ─── نشر على فيسبوك عبر Graph API ──────────────────────────────────

def post_to_facebook(message: str) -> str:
    url = f"https://graph.facebook.com/v19.0/{os.environ['FB_PAGE_ID']}/feed"
    payload = {
        "message": message,
        "access_token": os.environ["FB_PAGE_ACCESS_TOKEN"],
    }
    try:
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("id")
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"❌ فشل النشر على فيسبوك (HTTP {exc.response.status_code}): {exc.response.text}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"❌ خطأ في الاتصال بفيسبوك: {exc}") from exc


# ─── تسجيل المنشور في ملف CSV ───────────────────────────────────────

def log_post(post_id: str, message: str) -> None:
    log_file = "logs/posts_log.csv"
    file_exists = os.path.isfile(log_file)
    os.makedirs("logs", exist_ok=True)
    now      = datetime.datetime.now()
    week_num = get_week_number(now)
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "post_id", "week_number", "month_number", "day", "hour", "content_preview", "status"])
        writer.writerow([
            now.isoformat(),
            post_id,
            week_num,
            get_month_number(week_num),
            DAYS_AR[now.weekday()],
            now.hour,
            message[:100] + "...",
            "success",
        ])


# ─── إشعار بريدي عبر SMTP ───────────────────────────────────────────

def send_email_notification(post_id: str, message: str) -> None:
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASSWORD"]
    recipient  = NOTIFICATION_EMAIL

    now      = datetime.datetime.now()
    week_num = get_week_number(now)

    msg = MIMEText(
        f"✅ تم النشر بنجاح على فيسبوك!\n\n"
        f"🆔 معرف المنشور: {post_id}\n"
        f"🕐 الوقت: {now.strftime('%Y-%m-%d %H:%M')}\n"
        f"📅 اليوم: {DAYS_AR[now.weekday()]} | الأسبوع: {week_num} | الشهر: {get_month_number(week_num)}\n\n"
        f"📝 المحتوى:\n{message}",
        "plain",
        "utf-8",
    )
    msg["Subject"] = f"✅ Boncoin — نشر جديد [{now.strftime('%H:%M')}]"
    msg["From"] = smtp_user
    msg["To"]   = recipient

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"📧 تم إرسال البريد بنجاح إلى: {recipient}")
    except smtplib.SMTPAuthenticationError:
        print("⚠️ تعذّر إرسال البريد: خطأ مصادقة SMTP — تحقّق من SMTP_PASSWORD (App Password لـ Gmail)")
    except smtplib.SMTPException as exc:
        print(f"⚠️ تعذّر إرسال البريد: {exc}")


# ─── الدالة الرئيسية ────────────────────────────────────────────────────

if __name__ == "__main__":
    now      = datetime.datetime.now()
    week_num = get_week_number(now)
    print(f"🚀 بدء توليد المنشور — {DAYS_AR[now.weekday()]} الساعة {now.hour}:00 | الأسبوع {week_num} | الشهر {get_month_number(week_num)}")

    post_content = generate_post()
    print(f"\n✍️ المحتوى المولّد:\n{post_content}\n")

    print("📤 النشر على فيسبوك...")
    post_id = post_to_facebook(post_content)
    print(f"✅ تم النشر! معرف المنشور: {post_id}")

    log_post(post_id, post_content)
    print("📝 تم التسجيل في logs/posts_log.csv")

    send_email_notification(post_id, post_content)

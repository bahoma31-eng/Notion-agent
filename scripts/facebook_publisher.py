#!/usr/bin/env python3
"""
نظام النشر التلقائي على فيسبوك — مطعم الركن الجميل
يولّد محتوى تسويقياً عبر GitHub Models وينشره على صفحة فيسبوك.
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

# ─── الـ Prompt الخاص بتوليد المحتوى ────────────────────────────────────

SYSTEM_PROMPT = """
أنت خبير تسويق لمطعم "الركن الجميل" في مارافال، وهران، الجزائر.
مهمتك كتابة منشورات تسويقية جذابة على فيسبوك تمزج بين:
- اللغة العربية الفصحى البسيطة
- اللهجة الجزائرية الوهرانية الأصيلة

قواعد المنشور:
- الطول: بين 80 و 150 كلمة
- يبدأ بجملة تشويقية أو سؤال جذاب
- يذكر اسم المطعم "الركن الجميل" بشكل طبيعي
- يذكر الموقع "مارافال، وهران" مرة واحدة
- يحتوي على دعوة للزيارة أو الطلب (call to action)
- ينتهي بـ 3-5 هاشتاقات مناسبة (#الركن_الجميل #وهران #مطاعم_وهران ...)
- يتنوع بين: عروض، وجبات، أجواء المطعم، مناسبات، وجبات الإفطار/الغداء/العشاء
- لا يكرر نفس الفكرة في منشورين متتاليين
"""


# ─── توليد المنشور عبر GitHub Models ────────────────────────────────────

def generate_post() -> str:
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=os.environ["GH_TOKEN"],
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "اكتب منشوراً تسويقياً جديداً ومختلفاً للتاريخ والوقت: "
                        f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    ),
                },
            ],
            max_tokens=400,
            temperature=0.9,
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
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "post_id", "content_preview", "status"])
        writer.writerow([
            datetime.datetime.now().isoformat(),
            post_id,
            message[:100] + "...",
            "success",
        ])


# ─── إشعار بريدي عبر SMTP ───────────────────────────────────────────

def send_email_notification(post_id: str, message: str) -> None:
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASSWORD"]
    recipient  = NOTIFICATION_EMAIL  # ✅ عنوان الاستلام المحدد

    msg = MIMEText(
        f"✅ تم النشر بنجاح على فيسبوك!\n\n"
        f"🆔 معرف المنشور: {post_id}\n"
        f"🕐 الوقت: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"📝 المحتوى:\n{message}",
        "plain",
        "utf-8",
    )
    msg["Subject"] = (
        f"✅ نشر جديد — الركن الجميل [{datetime.datetime.now().strftime('%H:%M')}]"
    )
    msg["From"] = smtp_user
    msg["To"]   = recipient  # ✅ يرسل لـ bahoma31@gmail.com

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"📧 تم إرسال البريد بنجاح إلى: {recipient}")
    except smtplib.SMTPAuthenticationError:
        # ❗ خطأ مصادقة — غالباً SMTP_PASSWORD غير صحيح أو لم يُفعّل App Password
        print("⚠️ تعذّر إرسال البريد: خطأ مصادقة SMTP — تحقّق من SMTP_PASSWORD (App Password لـ Gmail)")
    except smtplib.SMTPException as exc:
        print(f"⚠️ تعذّر إرسال البريد: {exc}")


# ─── الدالة الرئيسية ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 بدء توليد المنشور...")
    post_content = generate_post()
    print(f"✍️ المحتوى المولّد:\n{post_content}\n")

    print("📤 النشر على فيسبوك...")
    post_id = post_to_facebook(post_content)
    print(f"✅ تم النشر! معرف المنشور: {post_id}")

    log_post(post_id, post_content)
    print("📝 تم التسجيل في logs/posts_log.csv")

    send_email_notification(post_id, post_content)

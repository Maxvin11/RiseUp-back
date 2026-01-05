import os
import sys
import time
import requests
from datetime import timedelta

import django
from django.utils import timezone
from django.db import close_old_connections

# ============================================
# 0) DJANGO SETUP (MUHIM: importlardan oldin)
# ============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "riseup.settings")
django.setup()

from django.conf import settings
from core.models import Task  # django.setup() dan keyin!

# ============================================
# 1) BOT TOKEN (ENG TO‘G‘RI: .env / settings)
# ============================================
BOT_TOKEN = getattr(settings, "BOT_TOKEN", None) or os.getenv("BOT_TOKEN")

# ============================================
# 2) HELPERS
# ============================================
def format_datetime(dt):
    if not dt:
        return "—"
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return timezone.localtime(dt).strftime("%d.%m.%Y • %H:%M")


def send_task_to_telegram(task: Task) -> bool:
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN topilmadi (.env yoki settings.py).")
        return False

    profile = getattr(task.user, "profile", None)
    if not profile or not profile.telegram_id:
        print(f"⚠️ Task #{task.id} userida telegram_id yo'q.")
        return False

    chat_id = profile.telegram_id

    type_map = {
        "short": "Qisqa javob",
        "mcq": "Ko‘p tanlov",
        "checkbox": "Checkbox",
    }

    lines = []
    lines.append("🌸 *Rejalashtirilgan savol vaqti keldi!*")
    lines.append("")
    lines.append(f"🆔 *Task #{task.id}*")
    lines.append(f"❓ *Savol:* {task.title}")
    lines.append(f"🔁 *Turi:* {type_map.get(task.type, task.type)}")

    if task.category:
        lines.append(f"🏷 *Kategoriya:* {task.category}")

    if task.scheduled_time:
        lines.append(f"📅 *Vaqti:* {format_datetime(task.scheduled_time)}")

    lines.append("")
    lines.append("✍️ Javobingizni *shu xabarga reply qilib* yozing.")
    lines.append("ℹ️ /task orqali barcha savollaringizni ko‘rishingiz mumkin.")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "\n".join(lines),
        "parse_mode": "Markdown",
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"✅ Task #{task.id} {chat_id} ga yuborildi.")
            return True
        print(f"❌ Telegram error: {resp.text}")
        return False
    except Exception as e:
        print(f"❌ Telegram request error: {e}")
        return False


# ============================================
# 3) LOOP
# ============================================
WINDOW_MINUTES = 2

def main_loop():
    print("🚀 send_tasks.py ishga tushdi. Har 60 sekundda tekshiradi...")

    while True:
        try:
            close_old_connections() 

            now = timezone.now()
            window_start = now - timedelta(minutes=WINDOW_MINUTES)

            tasks = (
                Task.objects.filter(
                    scheduled_time__isnull=False,
                    scheduled_time__gt=window_start,
                    scheduled_time__lte=now,
                    sent_to_telegram=False,
                    user__profile__telegram_id__isnull=False,
                )
                .select_related("user", "user__profile")
                .prefetch_related("options")
            )

            if tasks.exists():
                print(f"⏰ {tasks.count()} ta task topildi.")
            else:
                print("🔎 Task topilmadi.")

            for task in tasks:
                if send_task_to_telegram(task):
                    task.sent_to_telegram = True
                    task.save(update_fields=["sent_to_telegram"])

            time.sleep(60)

        except Exception as e:
            print("❌ LOOP ERROR:", e)
            time.sleep(10)

if __name__ == "__main__":
    main_loop()

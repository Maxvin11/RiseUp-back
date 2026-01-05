import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand

from core.models import Course, Lesson


class Command(BaseCommand):
    help = "Seed Course/Lesson data from Frontend/bolimlar/progress.html"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing courses and lessons before seeding",
        )
        parser.add_argument(
            "--source",
            default="Frontend/bolimlar/progress.html",
            help="Path to progress.html",
        )

    def handle(self, *args, **options):
        source_path = Path(options["source"])
        if not source_path.exists():
            self.stderr.write(f"Source not found: {source_path}")
            return

        if options["reset"]:
            Lesson.objects.all().delete()
            Course.objects.all().delete()

        raw = source_path.read_text(encoding="utf-8")
        marker = "// Filter tugmalar"
        start = raw.find("let DATA =")
        if start == -1:
            start = raw.find("const DATA =")
        end = raw.find(marker)
        if start == -1 or end == -1 or end <= start:
            self.stderr.write("DATA block not found in progress.html")
            return

        data_js = raw[start:end]
        data_js = data_js.split("const DATA =", 1)[1].strip()
        if data_js.endswith(";"):
            data_js = data_js[:-1]

        # remove JS comments
        data_js = re.sub(r"//.*", "", data_js)
        data_js = re.sub(r"/\*.*?\*/", "", data_js, flags=re.DOTALL)
        # quote keys
        data_js = re.sub(
            r'([{\[,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:',
            r'\1"\2":',
            data_js,
        )
        # remove trailing commas
        data_js = re.sub(r",(\s*[}\]])", r"\1", data_js)

        try:
            data = json.loads(data_js)
        except json.JSONDecodeError as exc:
            self.stderr.write(f"Failed to parse DATA: {exc}")
            return

        directions = data.get("directions", [])
        created_courses = 0
        created_lessons = 0

        for direction in directions:
            title = direction.get("title") or "Untitled"
            desc = direction.get("desc") or ""

            course, _ = Course.objects.get_or_create(
                title=title,
                defaults={"description": desc, "is_active": True},
            )
            if course.description != desc:
                course.description = desc
                course.save(update_fields=["description"])

            lessons = direction.get("lessons", [])
            for idx, lesson_data in enumerate(lessons, start=1):
                lesson_title = lesson_data.get("title") or f"{title} - {idx}"
                content = lesson_data.get("content") or ""
                level = lesson_data.get("level") or ""
                duration = lesson_data.get("duration") or ""
                video_id = lesson_data.get("videoId") or ""
                bullets = lesson_data.get("bullets") or []
                task = lesson_data.get("task") or ""

                lesson, created = Lesson.objects.get_or_create(
                    course=course,
                    order=idx,
                    defaults={
                        "title": lesson_title,
                        "content": content,
                        "level": level,
                        "duration": duration,
                        "video_id": video_id,
                        "bullets": bullets,
                        "task": task,
                    },
                )
                if not created:
                    lesson.title = lesson_title
                    lesson.content = content
                    lesson.level = level
                    lesson.duration = duration
                    lesson.video_id = video_id
                    lesson.bullets = bullets
                    lesson.task = task
                    lesson.save()
                else:
                    created_lessons += 1

            created_courses += 1

        self.stdout.write(
            f"Seed done: courses={created_courses}, lessons={created_lessons}"
        )

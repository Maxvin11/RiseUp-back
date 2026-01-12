from django.contrib import admin
from .models import Task, Option, Course, Lesson, Video, LessonProgress


class OptionInline(admin.TabularInline):
    model = Option
    extra = 1

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'category', 'user', 'created_at')
    list_filter = ('type', 'category', 'created_at')
    search_fields = ('title', 'category', 'user__username')
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'task', 'correct')
    list_filter = ('correct',)
    search_fields = ('text', 'task__title')


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ("title", "order")
    ordering = ("order",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "lessons_count")
    list_filter = ("is_active",)
    search_fields = ("title",)
    inlines = [LessonInline]

    def lessons_count(self, obj):
        return obj.lessons.count()


class VideoInline(admin.TabularInline):
    model = Video
    extra = 0
    fields = ("title", "order")
    ordering = ("order",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    inlines = [VideoInline]
    ordering = ("course", "order")


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "order")
    list_filter = ("lesson",)
    search_fields = ("title", "lesson__title")
    ordering = ("lesson", "order")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "completed", "completed_at")
    list_filter = ("completed", "lesson__course")
    search_fields = ("user__username", "lesson__title", "lesson__course__title")

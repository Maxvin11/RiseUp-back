from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
import uuid
import os


def avatar_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}" 
    return os.path.join("avatars", filename)

class UserStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="stats")
    total_points = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)

    last_daily_bonus = models.DateField(null=True, blank=True)

    def get_accuracy(self):
        total = self.correct_answers + self.wrong_answers
        if total > 0:
            return round((self.correct_answers / total) * 100, 2)
        return 0.0
    
    @property
    def success_rate(self):
        return self.get_accuracy()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    telegram_id = models.CharField(max_length=32, null=True, blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_to, null=True, blank=True)
 

    def __str__(self):
        return f"{self.user.username} profile"


class Task(models.Model):
    TASK_TYPES = (
        ('short', 'Short Answer'),
        ('mcq', 'Multiple Choice'), 
        ('checkbox', 'Checkbox'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TASK_TYPES)
    category = models.CharField(max_length=100, blank=True, null=True)
    correct_short = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)

    created_by_admin = models.BooleanField(default=False)

    sent_to_telegram = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Option(models.Model):
    task = models.ForeignKey(Task, related_name="options", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'correct' if self.correct else 'wrong'})"
    



class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    badge = models.CharField(
        max_length=100,
        blank=True,
        help_text="Qisqa Beydj: Bestseller, New, Pro"
    )

    cover_image = models.ImageField(
        upload_to="courses/covers/",
        blank=True,
        null=True
    )

    cover_url = models.URLField(
        blank=True,
        help_text="Если обложка хранится внешне (CDN)"
    )

    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Список тегов, например: ['python', 'backend']"
    )

    is_free = models.BooleanField(default=False)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    gradient = models.CharField(
        max_length=100,
        blank=True,
        help_text="CSS gradient или ключ темы"
    )

    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, related_name="lessons", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    level = models.CharField(max_length=50, blank=True)
    duration = models.CharField(max_length=50, blank=True)
    video_id = models.CharField(max_length=32, blank=True)
    bullets = models.JSONField(default=list, blank=True)
    task = models.TextField(blank=True)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"
    


class Video(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    video = models.FileField(upload_to='videos/')
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']


    def __str__(self):
        return f"{self.lesson.title} - {self.title}"
    

class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True) 

    class Meta:
        unique_together = ('user', 'lesson')
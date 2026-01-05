from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, UserStats, Option, Profile, LessonProgress, Course
import base64
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import ( Task, Option, UserStats, Profile, Course, Lesson, Video, LessonProgress )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('id','username','email','password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "text", "correct"]

class TaskSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, required=False)

    class Meta:
        model = Task
        fields = ["id", "title", "type", "category", "correct_short", "created_at", "scheduled_time", "options"]

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        task = Task.objects.create(**validated_data)
        for opt in options_data:
            Option.objects.create(task=task, **opt)
        return task

    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)
        instance.title = validated_data.get("title", instance.title)
        instance.type = validated_data.get("type", instance.type)
        instance.category = validated_data.get("category", instance.category)
        instance.correct_short = validated_data.get("correct_short", instance.correct_short)
        instance.save()
        if options_data is not None:
            instance.options.all().delete()
            for opt in options_data:
                Option.objects.create(task=instance, **opt)
        return instance

class UserStatsSerializer(serializers.ModelSerializer):
    success_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = UserStats
        fields = ["total_points", "correct_answers", "wrong_answers", "success_rate"]


class ProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = ['avatar', 'avatar_url']
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    full_name = serializers.CharField(source='first_name', allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'profile']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError("New passwords do not match")
        return data



class VideoSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ["id", "title", "order", "video", "video_url"]

    def get_video_url(self, obj):
        """
        Frontendga to'liq URL kerak bo'ladi.
        """
        request = self.context.get("request")
        if not obj.video:
            return None
        if request:
            return request.build_absolute_uri(obj.video.url)
        return obj.video.url


class LessonSerializer(serializers.ModelSerializer):
    videos = VideoSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "course",
            "title",
            "content",
            "level",
            "duration",
            "video_id",
            "bullets",
            "task",
            "order",
            "videos",
            "is_completed",
            "is_locked",
        ]
        read_only_fields = ["id", "videos"]

    def get_is_completed(self, obj):
        return bool(getattr(obj, "_is_completed", False))

    def get_is_locked(self, obj):
        return bool(getattr(obj, "_is_locked", False))



class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    teacher_name = serializers.CharField(
        source="teacher.username",
        read_only=True
    )
    cover = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "badge",
            "cover_image",
            "cover_url",
            "cover",
            "tags",
            "is_free",
            "price",
            "gradient",
            "teacher",
            "teacher_name",
            "is_active",
            "created_at",
            "progress_percent",
            "lessons",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        """
        Если курс бесплатный — цена всегда 0
        """
        if attrs.get("is_free") is True:
            attrs["price"] = 0
        return attrs

    def get_cover(self, obj):
        request = self.context.get("request")
        if obj.cover_image:
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        if obj.cover_url:
            return obj.cover_url
        return ""

    def get_progress_percent(self, obj):
        value = getattr(obj, "_progress_percent", None)
        return 0 if value is None else value


# =========================
# LESSON PROGRESS
# =========================

class LessonProgressSerializer(serializers.ModelSerializer):
    """
    POST /api/lesson-progress/  body: { "lesson": 12, "completed": true }
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = LessonProgress
        fields = ["id", "user", "lesson", "completed", "completed_at"]
        read_only_fields = ["id", "user", "completed_at"]

    def validate(self, attrs):
        """
        Sen unique_together qilgansan.
        Bu validate faqat yangi record yaratishda "bor bo'lsa" deb tekshiradi.
        """
        request = self.context.get("request")
        user = request.user if request else None
        lesson = attrs.get("lesson")

        if user and lesson:
            if LessonProgress.objects.filter(user=user, lesson=lesson).exists():
                raise serializers.ValidationError(
                    "Siz bu lesson uchun progress yaratib bo‘lgansiz."
                )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else None

        # completed true bo'lsa vaqt yozamiz
        completed = validated_data.get("completed", False)
        completed_at = timezone.now() if completed else None

        obj = LessonProgress.objects.create(
            user=user,
            lesson=validated_data["lesson"],
            completed=completed,
            completed_at=completed_at
        )
        return obj

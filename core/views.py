from datetime import date

from django.contrib.auth import get_user_model, update_session_auth_hash
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


from .models import (
    Task, UserStats, Profile,
    Course, Lesson, Video,
    LessonProgress
)
from .serializers import (
    AdminUserSerializer,
    TaskSerializer,
    CourseSerializer, LessonSerializer, VideoSerializer,
    LessonProgressSerializer
)

User = get_user_model()

# =========================================================
# AUTH
# =========================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    name = (request.data.get('name') or '').strip()
    email = (request.data.get('email') or '').strip().lower()
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Email va parol kerak!'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Bu email allaqachon mavjud!'}, status=400)

    username = name.replace(' ', '_') if name else email.split('@')[0]
    orig = username
    i = 1
    while User.objects.filter(username=username).exists():
        username = f"{orig}{i}"
        i += 1

    user = User.objects.create_user(username=username, email=email, password=password)
    refresh = RefreshToken.for_user(user)
    return Response({
        'username': user.username,
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    email = (request.data.get('email') or '').strip().lower()
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Email va parol kerak!'}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'Bunday foydalanuvchi topilmadi!'}, status=400)

    if not user.check_password(password):
        return Response({'error': 'Parol noto‘g‘ri!'}, status=400)

    refresh = RefreshToken.for_user(user)
    return Response({
        'username': user.username,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'is_superuser': user.is_superuser
    })


# =========================================================
# TASK CRUD (SENIKINI SAQLAB QO'YDIM)
# =========================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_task(request):
    serializer = TaskSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_tasks(request):
    tasks = Task.objects.filter(user=request.user).order_by("-id")
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_task(request, pk):
    task = get_object_or_404(Task, id=pk, user=request.user)
    return Response(TaskSerializer(task).data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_task(request, pk):
    task = get_object_or_404(Task, id=pk, user=request.user)
    serializer = TaskSerializer(task, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_task(request, pk):
    task = get_object_or_404(Task, id=pk, user=request.user)
    task.delete()
    return Response({"message": "Deleted"}, status=204)


# =========================================================
# TELEGRAM LINK
# =========================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_telegram(request):
    telegram_id = request.data.get("telegram_id")

    if not telegram_id:
        return Response({"error": "telegram_id kerak!"}, status=400)

    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.telegram_id = str(telegram_id)
    profile.save()

    return Response({"message": "Telegram bog‘landi!"})


# =========================================================
# PANEL / HEALTH
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def panel(request):
    return Response({"message": "Welcome to your dashboard!"}, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def health_check(request):
    return Response({
        "status": "ok",
        "message": "API is working",
        "user": request.user.username if request.user.is_authenticated else "anonymous"
    })


# =========================================================
# STATS / BONUS / SETTINGS
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats(request):
    user = request.user
    stats_obj, _ = UserStats.objects.get_or_create(user=user)

    user_tasks = Task.objects.filter(user=user)
    total_tasks = user_tasks.count()
    
    tasks_data = {
        "total": total_tasks,
        "by_type": list(user_tasks.values("type").annotate(count=Count("id")).order_by("-count")) if total_tasks else [],
        "by_category": list(user_tasks.values("category").annotate(count=Count("id")).order_by("-count")) if total_tasks else [],
        "by_date": list(user_tasks.values("created_at__date").annotate(count=Count("id")).order_by("created_at__date")) if total_tasks else [],
    }

    total_answers = stats_obj.correct_answers + stats_obj.wrong_answers
    accuracy = (stats_obj.correct_answers / total_answers * 100) if total_answers else 0

    return Response({
        "user_stats": {"total_points": stats_obj.total_points, "success_rate": round(accuracy, 2)},
        "answers": {
            "correct": stats_obj.correct_answers,
            "wrong": stats_obj.wrong_answers,
            "total": total_answers,
            "accuracy": round(accuracy, 2)
        },
        "tasks": tasks_data,
        "user_info": {"username": user.username, "email": user.email}
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_stats(request):
    is_correct_raw = request.data.get('correct', False)

    if isinstance(is_correct_raw, bool):
        is_correct = is_correct_raw
    elif isinstance(is_correct_raw, str):
        is_correct = is_correct_raw.lower() == 'true'
    elif isinstance(is_correct_raw, int):
        is_correct = bool(is_correct_raw)
    else:
        is_correct = False

    stats_obj, _ = UserStats.objects.get_or_create(user=request.user)

    if is_correct:
        stats_obj.correct_answers += 1
        action = "correct"
    else:
        stats_obj.wrong_answers += 1
        action = "wrong"

    stats_obj.save()

    total_answers = stats_obj.correct_answers + stats_obj.wrong_answers
    accuracy = (stats_obj.correct_answers / total_answers * 100) if total_answers else 0

    return Response({
        'message': f'{action} answer recorded',
        'stats': {
            'correct_answers': stats_obj.correct_answers,
            'wrong_answers': stats_obj.wrong_answers,
            'total_answers': total_answers,
            'accuracy': round(accuracy, 2),
            'total_points': stats_obj.total_points
        }
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def daily_bonus(request):
    user = request.user
    today = timezone.now().date()

    stats_obj, _ = UserStats.objects.get_or_create(user=user)

    if stats_obj.last_daily_bonus == today:
        return Response({
            "message": "Bugun bo'nus obo'ldiz.",
            "total_points": stats_obj.total_points,
            "bonus_received": False
        })

    stats_obj.total_points += 10
    stats_obj.last_daily_bonus = today
    stats_obj.save()

    return Response({
        "message": "Kunlik bo'nus berildi!",
        "total_points": stats_obj.total_points,
        "bonus_received": True
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    Profile.objects.get_or_create(user=request.user)
    return Response({
        "first_name": request.user.first_name or "",
        "default_avatar": f"https://api.dicebear.com/7.x/bottts/svg?seed={request.user.username}"
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_name(request):
    request.user.first_name = (request.data.get("name", "") or "").strip()
    request.user.save()
    return Response({"success": True, "first_name": request.user.first_name})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    old = request.data.get("old_password")
    new1 = request.data.get("new_password")
    new2 = request.data.get("confirm_password")

    if not request.user.check_password(old):
        return Response({"error": "Hozirgi paro'l noto'g'ri"}, status=400)
    if new1 != new2:
        return Response({"error": "Paro'lar mos emas"}, status=400)
    if not new1 or len(new1) < 6:
        return Response({"error": "Paro'l juda qisqa"}, status=400)

    request.user.set_password(new1)
    request.user.save()
    update_session_auth_hash(request, request.user)

    return Response({"success": True, "message": "Paro'l o'zgardi"})


# =========================================================
# ADMIN PERMISSION + ADMIN ENDPOINTS
# =========================================================

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.is_staff)
        )


def _parse_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(value, int):
        return bool(value)
    return default


def _annotate_courses_progress(user, courses):
    courses = list(courses)

    lesson_ids = list(
        Lesson.objects.filter(course__in=courses)
        .values_list("id", flat=True)
    )

    completed_ids = set(
        LessonProgress.objects.filter(
            user=user, completed=True, lesson_id__in=lesson_ids
        ).values_list("lesson_id", flat=True)
    )

    for course in courses:
        lessons = list(course.lessons.all().order_by("order"))
        completed_count = 0

        for i, lesson in enumerate(lessons):
            lesson._is_completed = lesson.id in completed_ids
            lesson._is_locked = False if i == 0 else not lessons[i-1]._is_completed
            if lesson._is_completed:
                completed_count += 1

        course._lessons_count = len(lessons)
        course._completed_count = completed_count
        course._progress_percent = round((completed_count / len(lessons)) * 100) if lessons else 0

    return courses


def _is_lesson_locked(user, lesson):
    lessons = list(lesson.course.lessons.all().order_by("order"))
    if not lessons:
        return False

    completed_ids = set(
        LessonProgress.objects.filter(
            user=user, completed=True, lesson__course=lesson.course
        ).values_list("lesson_id", flat=True)
    )

    for i, l in enumerate(lessons):
        if l.id == lesson.id:
            if i == 0:
                return False
            return lessons[i - 1].id not in completed_ids
    return False


@api_view(['GET'])
@permission_classes([IsSuperUser])
def admin_dashboard(request):
    today = date.today()
    return Response({
        "total_users": User.objects.count(),
        "telegram_connected": User.objects.filter(profile__telegram_id__isnull=False).count(),
        "total_tasks": Task.objects.count(),
        "today_tasks": Task.objects.filter(scheduled_time__date=today).count(),
        "total_courses": Course.objects.count(),
        "total_lessons": Lesson.objects.count(),
    })


@api_view(['GET'])
@permission_classes([IsSuperUser])
def admin_users(request):
    users = (
        User.objects
        .select_related('profile', 'stats')
        .annotate(tasks_count=Count('task'))
        .order_by('-date_joined')
    )

    serializer = AdminUserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def admin_tasks(request):
    qs = Task.objects.select_related('user')

    sent = request.GET.get('sent')
    dt = request.GET.get('date')

    if sent in ['true', 'false']:
        qs = qs.filter(sent_to_telegram=(sent == 'true'))

    if dt:
        qs = qs.filter(scheduled_time__date=dt)

    return Response([
        {
            "id": t.id,
            "user_username": t.user.username,
            "user_email": t.user.email,
            "title": t.title,
            "type": t.type,
            "category": t.category,
            "scheduled_time": t.scheduled_time,
            "sent_to_telegram": t.sent_to_telegram,
        }
        for t in qs
    ])


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def admin_delete_task(request, pk):
    Task.objects.filter(pk=pk).delete()
    return Response({"success": True})


@api_view(['DELETE'])
@permission_classes([IsSuperUser])
def admin_delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)

    if user.id == request.user.id:
        return Response({"error": "O'zingizni o'chira olmaysiz"}, status=400)

    user.delete()
    return Response({"success": True})



# =========================================================
# USER — COURSES
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def course_list(request):
    """
    Список активных курсов (user)
    """
    qs = (
        Course.objects
        .filter(is_active=True)
        .prefetch_related("lessons__videos")
        .order_by("title")
    )
    courses = _annotate_courses_progress(request.user, qs)
    serializer = CourseSerializer(courses, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def course_detail(request, pk):
    """
    Детали одного курса (user)
    """
    course = get_object_or_404(
        Course.objects.prefetch_related("lessons__videos"),
        pk=pk,
        is_active=True
    )
    _annotate_courses_progress(request.user, [course])
    serializer = CourseSerializer(course, context={"request": request})
    return Response(serializer.data)


# =========================================================
# USER — LESSONS / VIDEOS
# =========================================================

def _is_lesson_locked(user, lesson):
    """
    Блокировка уроков по порядку.
    Первый урок всегда доступен.
    """
    prev_lessons = (
        Lesson.objects
        .filter(course=lesson.course, order__lt=lesson.order)
        .order_by("order")
    )

    for prev in prev_lessons:
        if not LessonProgress.objects.filter(
            user=user,
            lesson=prev,
            completed=True
        ).exists():
            return True
    return False


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_lesson_detail(request, lesson_id):
    """
    Детали урока (user)
    """
    lesson = get_object_or_404(
        Lesson.objects.prefetch_related("videos"),
        id=lesson_id
    )

    if _is_lesson_locked(request.user, lesson):
        return Response(
            {"error": "Bu dars hozircha yopiq."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = LessonSerializer(lesson, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def lesson_videos(request, lesson_id):
    """
    Видео урока (user)
    """
    lesson = get_object_or_404(
        Lesson.objects.prefetch_related("videos"),
        id=lesson_id
    )

    if _is_lesson_locked(request.user, lesson):
        return Response(
            {"error": "Bu dars hozircha yopiq."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = VideoSerializer(
        lesson.videos.all().order_by("order"),
        many=True,
        context={"request": request}
    )

    return Response({
        "lesson_id": lesson.id,
        "lesson_title": lesson.title,
        "videos": serializer.data
    })


# =========================================================
# USER — PROGRESS
# =========================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def lesson_progress(request):
    """
    GET  -> список progress пользователя
    POST -> отметить lesson completed / not completed
    """
    user = request.user

    if request.method == "GET":
        qs = (
            LessonProgress.objects
            .filter(user=user)
            .select_related("lesson")
            .order_by("-completed_at")
        )
        serializer = LessonProgressSerializer(qs, many=True)
        return Response(serializer.data)

    # POST (upsert)
    lesson_id = request.data.get("lesson")
    completed = bool(request.data.get("completed", True))

    if not lesson_id:
        return Response(
            {"error": "lesson field required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    lesson = get_object_or_404(Lesson, id=lesson_id)

    if completed and _is_lesson_locked(user, lesson):
        return Response(
            {"error": "Bu dars hozircha yopiq."},
            status=status.HTTP_403_FORBIDDEN
        )

    obj, _ = LessonProgress.objects.get_or_create(
        user=user,
        lesson=lesson
    )

    obj.completed = completed
    obj.completed_at = timezone.now() if completed else None
    obj.save()

    return Response(
        LessonProgressSerializer(obj).data,
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_video(request, video_id):
    """
    Видео завершено -> lesson completed
    """
    video = get_object_or_404(Video, id=video_id)
    lesson = video.lesson

    if _is_lesson_locked(request.user, lesson):
        return Response(
            {"error": "Bu dars hozircha yopiq."},
            status=status.HTTP_403_FORBIDDEN
        )

    lp, _ = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    lp.completed = True
    lp.completed_at = timezone.now()
    lp.save()

    return Response(
        {"message": "Video completed successfully"},
        status=status.HTTP_200_OK
    )


# =========================================================
# ADMIN — COURSES CRUD
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperUser])
def admin_realtime(request):
    return Response({
        "online_users": 1,
        "rpm": 0,
        "db_latency_ms": 0,
        "queue_pending": 0,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSuperUser])
def admin_courses(request):
    include_inactive = _parse_bool(request.query_params.get("include_inactive"))
    qs = Course.objects
    if not include_inactive:
        qs = qs.filter(is_active=True)
    qs = (
        qs
        .prefetch_related("lessons__videos")
        .order_by("title")
    )
    serializer = CourseSerializer(qs, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperUser])
def course_create(request):
    serializer = CourseSerializer(
        data=request.data,
        context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated, IsSuperUser])
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)

    serializer = CourseSerializer(
        course,
        data=request.data,
        partial=True,
        context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsSuperUser])
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# =========================================================
# ADMIN — LESSONS CRUD
# =========================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsSuperUser])
def admin_lessons(request):
    if request.method == "GET":
        qs = (
            Lesson.objects
            .select_related("course")
            .order_by("course_id", "order")
        )
        serializer = LessonSerializer(
            qs,
            many=True,
            context={"request": request}
        )
        return Response(serializer.data)

    serializer = LessonSerializer(
        data=request.data,
        context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsSuperUser])
def admin_lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)

    if request.method == "GET":
        return Response(
            LessonSerializer(lesson, context={"request": request}).data
        )

    if request.method == "PUT":
        serializer = LessonSerializer(
            lesson,
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    lesson.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsSuperUser])
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')

    data = []
    for u in users:
        profile = getattr(u, "profile", None)
        stats = getattr(u, "stats", None)
        data.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_staff": u.is_staff,
            "telegram_linked": bool(profile and profile.telegram_id),
            "tasks_count": u.task_set.count(),
            "total_points": stats.total_points if stats else 0,
            "created_at": u.date_joined,
            "last_login": u.last_login,
        })

    return Response(data)

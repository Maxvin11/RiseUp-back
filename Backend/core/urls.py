from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Auth
    path('auth/register/', views.register_user),
    path('auth/login/', views.login_user, name="login"),
    path('auth/panel/', views.panel),

    # Telegram linking
    path('auth/link-telegram/', views.link_telegram),

    # Statistic uchun
    path("stats/", views.stats),
    path("stats/update/", views.update_stats),
    path('health/', views.health_check, name='health_check'),

    # daily bonus
    path("daily-bonus/", views.daily_bonus),

    # settings profile
    path('settings/profile/', views.get_profile, name='get_profile'),
    path('settings/name/', views.update_name, name='update_name'),
    path('settings/password/', views.change_password, name='change_password'),

    # Tasks
    path("tasks/", views.list_tasks),
    path("tasks/create/", views.create_task),
    path("tasks/<int:pk>/", views.get_task),
    path("tasks/<int:pk>/update/", views.update_task),
    path("tasks/<int:pk>/delete/", views.delete_task),  

    # Admin panel
    path('admin/dashboard/', views.admin_dashboard),
    path('admin/users/', views.admin_users),
    path('admin/tasks/', views.admin_tasks),
    path('admin/tasks/<int:pk>/', views.admin_delete_task),
    path('admin/users/<int:pk>/', views.admin_delete_user),
    path("admin/realtime/", views.admin_realtime),
    path("admin/courses/", views.admin_courses),

    # Courses (CRUD)
    path("admin/courses/create/", views.course_create, name="course_create"),
    path("admin/courses/<int:pk>/update/", views.course_update, name="course_update"),
    path("admin/courses/<int:pk>/delete/", views.course_delete, name="course_delete"),

    # Lessons (CRUD)
    path("admin/lessons/", views.admin_lessons, name="admin_lessons"),
    path("admin/lessons/<int:pk>/", views.admin_lesson_detail, name="admin_lesson_detail"),

    # =====================================================
    # USER API
    # =====================================================

    # Courses
    path("courses/", views.course_list, name="course_list"),
    path("courses/<int:pk>/", views.course_detail, name="course_detail"),

    # Lessons / Videos
    path("lessons/<int:lesson_id>/", views.user_lesson_detail, name="user_lesson_detail"),
    path("lessons/<int:lesson_id>/videos/", views.lesson_videos, name="lesson_videos"),

    # Progress
    path("lesson-progress/", views.lesson_progress, name="lesson_progress"),
    path("videos/<int:video_id>/complete/", views.complete_video, name="complete_video"),
]

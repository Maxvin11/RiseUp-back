from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from datetime import date

from .models import Profile, UserStats

@receiver(post_save, sender=User)
def create_profile_and_stats(sender, instance, created, **kwargs):
    if not created:
        return

    Profile.objects.get_or_create(user=instance)

    UserStats.objects.get_or_create(
        user=instance,
        defaults={
            "total_points": 50,
            "last_daily_bonus": date.today(),
        }
    )
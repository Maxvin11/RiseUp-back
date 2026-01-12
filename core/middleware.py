from datetime import date

class DailyBonusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = request.user
        if not user.is_authenticated:
            return response

        stats = getattr(user, "stats", None)
        if not stats:
            return response

        today = date.today()

        if stats.last_daily_bonus != today:
            stats.total_points += 1
            stats.last_daily_bonus = today
            stats.save(update_fields=["total_points", "last_daily_bonus"])

        return response

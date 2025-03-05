import datetime
from django.conf import settings
from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin

class AutoLogoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return

        # Mendapatkan waktu terakhir aktivitas
        last_activity = request.session.get('last_activity')

        # Jika waktu terakhir aktivitas tidak ada, setel sekarang
        if last_activity:
            now = datetime.datetime.now()
            elapsed_time = (now - datetime.datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S')).seconds

            # Jika waktu sudah melebihi batas yang ditentukan, logout otomatis
            if elapsed_time > settings.SESSION_COOKIE_AGE:
                logout(request)
                return

        # Update waktu terakhir aktivitas
        request.session['last_activity'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

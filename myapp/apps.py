from django.apps import AppConfig

# otomatis update

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        import myapp.signals  # Pastikan ini merujuk pada nama aplikasi Anda
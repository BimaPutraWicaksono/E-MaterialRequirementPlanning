from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = "Seed the User table with test data"

    users = [
        {"username": "admin", "password": "1234", "group": "Admin"},
        {"username": "karyawan", "password": "1234", "group": "Karyawan"},
        {"username": "supervisor", "password": "1234", "group": "Supervisor"},
        {"username": "senior_supervisor", "password": "1234", "group": "SeniorSupervisor"},
        {"username": "manager", "password": "1234", "group": "Manager"},
        {"username": "factory_manager", "password": "1234", "group": "FactoryManager"},
    ]

    def handle(self, *args, **kwargs):
        group_names = list(set(user["group"] for user in self.users))

        # Buat grup jika belum ada
        for group_name in group_names:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Grup '{group_name}' berhasil dibuat!"))
            else:
                self.stdout.write(self.style.WARNING(f"Grup '{group_name}' sudah ada."))

        # Buat user dan hubungkan dengan grup
        for item in self.users:
            user, created = User.objects.get_or_create(username=item["username"])
            if created:
                user.set_password(item["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"User '{item['username']}' berhasil dibuat."))
            else:
                self.stdout.write(self.style.WARNING(f"User '{item['username']}' sudah ada. Password tidak diubah."))

            try:
                group = Group.objects.get(name=item["group"])
                user.groups.set([group])
                self.stdout.write(self.style.SUCCESS(f"User '{item['username']}' ditambahkan ke grup '{item['group']}'"))
            except Group.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Grup '{item['group']}' tidak ditemukan!"))

        self.stdout.write(self.style.SUCCESS("Proses seeding user selesai."))

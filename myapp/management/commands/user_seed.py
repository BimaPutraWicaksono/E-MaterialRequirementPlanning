import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = "Seed the User table with test data"

    users = [
        {
            "username": "admin",
            "password": "1234",
            "group": "Admin",
        },
        {
            "username": "karyawan",
            "password": "1234",
            "group": "Guest",
        },
        {
            "username": "supervisor",
            "password": "super123",
            "group": "Supervisor",
        },
        {
            "username": "senior_supervisor",
            "password": "senior123",
            "group": "Senior Supervisor",
        },
    ]

    groups = ["Admin", "Guest", "Supervisor", "Senior Supervisor"]

    def handle(self, *args, **kwargs):
        # Buat grup jika belum ada
        for group_name in self.groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Grup '{group_name}' berhasil dibuat!"))
            else:
                self.stdout.write(self.style.WARNING(f"Grup '{group_name}' sudah ada."))

        # Buat user dan hubungkan dengan grup
        for item in self.users:
            user, created = User.objects.get_or_create(username=item["username"])
            user.set_password(item["password"])
            user.save()

            try:
                group = Group.objects.get(name=item["group"])
                user.groups.set([group])
                self.stdout.write(self.style.SUCCESS(f"User '{item['username']}' ditambahkan ke grup '{item['group']}'"))
            except Group.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Grup '{item['group']}' tidak ditemukan!"))

        self.stdout.write(self.style.SUCCESS("Semua user berhasil ditambahkan!"))

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from myapp.models import Departement

User = get_user_model()

class Command(BaseCommand):
    help = "Seed the User table with test data and assign departments"

    users = [
        {"username": "admin", "password": "1234", "group": "Admin", "departement": "IT"},
        {"username": "karyawan", "password": "1234", "group": "Karyawan", "departement": "IT"},
        {"username": "supervisor", "password": "1234", "group": "Supervisor", "departement": "IT"},
        {"username": "senior_supervisor", "password": "1234", "group": "SeniorSupervisor", "departement": "IT"},
        {"username": "manager", "password": "1234", "group": "Manager", "departement": "IT"},
        {"username": "factory_manager", "password": "1234", "group": "FactoryManager", "departement": "IT"},
    ]

    def handle(self, *args, **kwargs):
        # Buat semua grup
        group_names = list(set(user["group"] for user in self.users))
        for group_name in group_names:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Grup '{group_name}' berhasil dibuat."))
            else:
                self.stdout.write(self.style.WARNING(f"Grup '{group_name}' sudah ada."))

        # Buat semua departemen
        dept_names = list(set(user["departement"] for user in self.users))
        for dept_name in dept_names:
            Departement.objects.get_or_create(name=dept_name)

        # Buat user dan hubungkan ke grup dan departemen
        for item in self.users:
            departement = Departement.objects.get(name=item["departement"])
            user, created = User.objects.get_or_create(username=item["username"], defaults={
                "departement": departement,
            })

            if created:
                user.set_password(item["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"User '{item['username']}' berhasil dibuat."))
            else:
                self.stdout.write(self.style.WARNING(f"User '{item['username']}' sudah ada. Password tidak diubah."))

            # Set departemen jika belum ada
            if not user.departement:
                user.departement = departement
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Departemen '{departement.name}' ditetapkan untuk user '{user.username}'."))

            # Set grup
            group = Group.objects.get(name=item["group"])
            user.groups.set([group])
            self.stdout.write(self.style.SUCCESS(f"User '{item['username']}' ditambahkan ke grup '{item['group']}'."))

        self.stdout.write(self.style.SUCCESS("Proses seeding user selesai."))

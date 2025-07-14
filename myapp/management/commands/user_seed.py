from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from myapp.models import Departement

User = get_user_model()

class Command(BaseCommand):
    help = "Seed the User table with test data and assign departments"

    def handle(self, *args, **kwargs):
        # Definisikan user tetap
        fixed_users = [
            {"username": "Rendi", "password": "1234", "group": "Admin", "departement": None},
            {"username": "Ninda", "password": "1234", "group": "Karyawan", "departement": "Stock Control"},
        ]

        # Grup yang akan dibuat
        roles = ['Admin', 'Karyawan', 'Supervisor', 'SeniorSupervisor', 'Manager', 'FactoryManager']
        for role in roles:
            Group.objects.get_or_create(name=role)

        # Buat fixed user: Admin dan Ninda
        for user_data in fixed_users:
            dept = None
            if user_data["departement"]:
                dept = Departement.objects.get(name=user_data["departement"])
            user, created = User.objects.get_or_create(username=user_data["username"], defaults={
                "departement": dept,
            })
            if created:
                user.set_password(user_data["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"✅ User '{user.username}' dibuat."))

            if dept and not user.departement:
                user.departement = dept
                user.save()

            group = Group.objects.get(name=user_data["group"])
            user.groups.set([group])
            self.stdout.write(self.style.SUCCESS(f"🔗 Grup '{group.name}' ditetapkan ke '{user.username}'"))

        # Daftar user tambahan berdasarkan departemen (tanpa Admin dan Stock Control)
        user_templates = {
            "Production": [
                {"username": "Nevara", "group": "Karyawan"},
                {"username": "Altisha", "group": "Supervisor"},
                {"username": "Praz", "group": "SeniorSupervisor"},
                {"username": "Amel", "group": "Manager"},
                {"username": "Afifah", "group": "FactoryManager"},
            ],
            "Maintenance": [
                {"username": "Diouf", "group": "Karyawan"},
                {"username": "Riza", "group": "Supervisor"},
                {"username": "Nala", "group": "SeniorSupervisor"},
                {"username": "Tasya", "group": "Manager"},
                {"username": "Muti", "group": "FactoryManager"},
            ],
            "Purchasing": [
                {"username": "Wildan", "group": "Karyawan"},
                {"username": "Vandy", "group": "Supervisor"},
                {"username": "Iemaduddin", "group": "SeniorSupervisor"},
                {"username": "Rizki", "group": "Manager"},
                {"username": "Marina", "group": "FactoryManager"},
            ],
        }

        for dept_name, users in user_templates.items():
            departement = Departement.objects.get(name=dept_name)
            for user_data in users:
                user, created = User.objects.get_or_create(username=user_data["username"], defaults={
                    "departement": departement,
                })
                if created:
                    user.set_password("1234")
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ User '{user.username}' dibuat untuk Departemen '{dept_name}'."))

                if not user.departement:
                    user.departement = departement
                    user.save()

                group = Group.objects.get(name=user_data["group"])
                user.groups.set([group])
                self.stdout.write(self.style.SUCCESS(f"🔗 Grup '{group.name}' ditetapkan ke '{user.username}'"))

        self.stdout.write(self.style.SUCCESS("🎉 Semua user berhasil disiapkan."))

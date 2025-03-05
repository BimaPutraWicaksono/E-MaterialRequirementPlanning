import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = 'Seed the User table with test data'

    user = [
        {
            'username': 'MTC',
            'password': 'adminmtc',
            'group': 'Admin',
            
        },  
        {
            'username': 'userMTC',
            'password': 'mtcmtc',
            'group': 'Guest',
            
        },   
    ]

    group=[
        "Admin", "Guest",
    ]

    def handle(self, *args, **kwargs):
        for i in self.group:
            Group.objects.create(name=i)
        
        for item in self.user:
            user, created = User.objects.update_or_create(
                username=item['username'],
            )
            user.set_password(item['password'])  # Set password correctly
            user.save()

            group = Group.objects.get(name=item['group'])
            user.groups.set([group])

        self.stdout.write(self.style.SUCCESS('Data added successfully!'))
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.http import JsonResponse

from .form import SignupForm, LoginForm
from .models import Departement


# Create your views here.
def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Incorrect username or password')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')

User = get_user_model()  # Ambil model User yang aktif (CustomUser kalau sudah di-swap)

@login_required
def daftar_akun(request):
    users = User.objects.all()
    groups = Group.objects.all()
    departements = Departement.objects.all()  # Tambahkan departement

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        username = request.POST.get('username')
        password = request.POST.get('password')
        group_id = request.POST.get('group')
        departement_id = request.POST.get('departement')  # Ambil departement

        if not username:
            messages.error(request, 'Username harus diisi.')
            return redirect('daftar_akun')

        if not password and not user_id:
            messages.error(request, 'Password harus diisi untuk pengguna baru.')
            return redirect('daftar_akun')

        if user_id:
            user = get_object_or_404(User, pk=user_id)
            user.username = username
            if password:
                user.set_password(password)
            user.groups.clear()
            user.groups.add(group_id)
            user.departement_id = departement_id  # Tambahkan departement
            user.save()
            messages.success(request, 'Akun berhasil diperbarui.')
        else:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username sudah digunakan.')
                return redirect('daftar_akun')
            user = User.objects.create_user(
                username=username,
                password=password,
                departement_id=departement_id  # Tambahkan saat buat user
            )
            group = Group.objects.get(id=group_id)
            user.groups.add(group)
            messages.success(request, 'Akun berhasil ditambahkan.')

        return redirect('daftar_akun')

    context = {
        'users': users,
        'groups': groups,
        'departements': departements,  # Kirim ke template
    }
    return render(request, 'account.html', context)

@login_required
def hapus_akun(request):
    if request.method == 'POST':
        user_id = request.POST.get('hapus_user_id')
        username = request.POST.get('username')
        email = request.POST.get('email')

        if not user_id and not username and not email:
            messages.error(request, 'ID, Username, atau Email tidak valid.')
            return redirect('daftar_akun')

        if user_id:
            user = get_object_or_404(User, pk=user_id)
        elif username:
            user = get_object_or_404(User, username=username)
        elif email:
            user = get_object_or_404(User, email=email)

        if user == request.user:
            messages.error(request, 'Anda tidak dapat menghapus akun yang sedang digunakan untuk login.')
            return redirect('daftar_akun')

        if user.groups.filter(name='Admin').exists():
            admin_count = User.objects.filter(groups__name='Admin').count()
            if admin_count <= 1:
                messages.error(request, 'Tidak bisa menghapus akun admin terakhir.')
                return redirect('daftar_akun')

        user.delete()
        messages.success(request, 'Akun berhasil dihapus.')
        return redirect('daftar_akun')

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def update_user_profile(request):
    if request.method == 'POST':
        user = request.user
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username:
            user.username = username

        if password:
            user.password = make_password(password)

        user.save()
        messages.success(request, "Akun berhasil diperbarui.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('/')

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .form import SignupForm, LoginForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# View untuk daftar akun
@login_required
def daftar_akun(request):
    users = User.objects.all()  # Mengambil semua pengguna dari model User
    groups = Group.objects.all()  # Mengambil semua group (seperti admin, user, dll.)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        username = request.POST.get('username')
        password = request.POST.get('password')
        group_id = request.POST.get('group')

        # Validasi input username dan password
        if not username:
            messages.error(request, 'Username harus diisi.')
            return redirect('daftar_akun')

        if not password and not user_id:  # Password harus diisi saat menambah user baru
            messages.error(request, 'Password harus diisi untuk pengguna baru.')
            return redirect('daftar_akun')

        if user_id:  # Edit akun
            user = get_object_or_404(User, pk=user_id)
            user.username = username
            if password:  # Jika password diisi, lakukan update
                user.set_password(password)
            user.groups.clear()  # Hapus group yang ada
            user.groups.add(group_id)  # Tambahkan group baru
            user.save()
            messages.success(request, 'Akun berhasil diperbarui.')
        else:  # Tambah akun baru
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username sudah digunakan. Pilih username lain.')
                return redirect('daftar_akun')
            user = User.objects.create_user(username=username, password=password)
            group = Group.objects.get(id=group_id)
            user.groups.add(group)
            messages.success(request, 'Akun berhasil ditambahkan.')

        return redirect('daftar_akun')

    context = {
        'users': users,
        'groups': groups,
    }
    return render(request, 'account.html', context)

# View untuk menghapus akun
from django.contrib.auth import get_user_model

@login_required
def hapus_akun(request):
    if request.method == 'POST':
        user_id = request.POST.get('hapus_user_id')
        username = request.POST.get('username')  # Opsi untuk menghapus berdasarkan username
        email = request.POST.get('email')  # Opsi untuk menghapus berdasarkan email
        
        # Validasi input yang harus ada
        if not user_id and not username and not email:
            messages.error(request, 'ID, Username, atau Email tidak valid.')
            return redirect('daftar_akun')

        # Hapus berdasarkan user_id, username, atau email
        if user_id:
            user = get_object_or_404(User, pk=user_id)
        elif username:
            user = get_object_or_404(User, username=username)
        elif email:
            user = get_object_or_404(User, email=email)

        # Periksa apakah user adalah pengguna yang sedang login
        if user == request.user:
            messages.error(request, 'Anda tidak dapat menghapus akun yang sedang digunakan untuk login.')
            return redirect('daftar_akun')

        # Periksa apakah user berada dalam group Admin
        if user.groups.filter(name='Admin').exists():
            # Hitung jumlah user yang berada di group Admin
            admin_count = User.objects.filter(groups__name='Admin').count()

            # Jika hanya ada satu admin, maka tidak boleh dihapus
            if admin_count <= 1:
                messages.error(request, 'Tidak bisa menghapus akun admin terakhir.')
                return redirect('daftar_akun')

        # Hapus user jika masih ada lebih dari satu admin dan bukan user yang sedang login
        user.delete()
        messages.success(request, 'Akun berhasil dihapus.')
        
        return redirect('daftar_akun')
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

import openpyxl
from openpyxl import Workbook
import pandas as pd

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from django.db import transaction
from django.contrib.auth.decorators import login_required

from .form import UploadFileForm
from .models import (
    PartName, ApplicatorPart, PartDesk,
    Load_applicator, LoadingPartResult
)

# Applicator 
@login_required()
def applicator(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            df = pd.read_excel(excel_file, engine='openpyxl')

            # Mendapatkan nama kolom
            columns = df.columns

            # Indeks kolom yang diinginkan (mulai dari kolom ke-6)
            start_col_index = 6
            step = 4  # Setiap kolom 4 langkah ke kanan

            # Proses baris dari B8 ke bawah untuk ApplicatorPart
            if len(df) > 6:
                applicator_values = df.iloc[6:, 1]  # Kolom B dimulai dari baris 8
            else:
                applicator_values = []

            # Ambil data hanya dari baris ke-5 (indeks 4) pada kolom yang ditentukan
            if len(df) > 3:
                part_names = df.iloc[3, start_col_index: start_col_index + step * 40: step]  # Ambil data dari baris ke-5 (indeks 4) untuk kolom-kolom yang ditentukan
            else:
                part_names = []

            # Simpan objek PartName dalam dictionary untuk digunakan kembali
            part_name_objects = {}
            for col_index, part_name_value in zip(range(start_col_index, start_col_index + step * 40, step), part_names):
                if pd.isna(part_name_value):  # Jika partName kosong, hentikan proses
                    break
                # Ubah part_name_value menjadi uppercase sebelum disimpan
                part_name_value_upper = part_name_value.upper()
                part_name, _ = PartName.objects.get_or_create(partName=part_name_value_upper)
                part_name_objects[col_index] = part_name

            # Proses untuk ApplicatorPart
            applicator_parts = {}
            for index in range(len(applicator_values)):
                applicator_value = applicator_values.iloc[index]
                if pd.notna(applicator_value):  # Pastikan nilai tidak NaN
                    applicator_part, _ = ApplicatorPart.objects.get_or_create(applicatorNumber=applicator_value)
                    applicator_parts[index] = applicator_part
                else:
                    applicator_part, _ = ApplicatorPart.objects.get_or_create(applicatorNumber=' ')
                    applicator_parts[index] = applicator_part

            # Proses untuk PartDesk
            col_index = start_col_index
            while col_index < len(columns):
                # Jika kolom part_name kosong, hentikan proses
                if col_index not in part_name_objects:
                    break

                # Ambil data untuk kolom saat ini
                if len(df) > 6:
                    part_number_values = df.iloc[6:, col_index]  # Kolom G dimulai dari baris 8
                    part_code_values = df.iloc[6:, col_index + 1]  # Kolom H dimulai dari baris 8
                    level_values = df.iloc[6:, col_index + 2]  # Kolom I dimulai dari baris 8
                    marking_values = df.iloc[6:, col_index + 3]  # Kolom J dimulai dari baris 8
                else:
                    part_number_values = []
                    part_code_values = []
                    level_values = []
                    marking_values = []

                # Ambil PartName untuk kolom ini
                part_name = part_name_objects.get(col_index, None)

                for index in range(len(part_number_values)):
                    applicator_part = applicator_parts.get(index, None)
                    part_number_value = part_number_values.iloc[index] if pd.notna(part_number_values.iloc[index]) else ' '
                    
                    # Menghilangkan desimal .0 pada partCode dan marking jika ada
                    part_code_value = str(part_code_values.iloc[index]).rstrip('.0') if pd.notna(part_code_values.iloc[index]) else ' '
                    marking_value = str(marking_values.iloc[index]).rstrip('.0') if pd.notna(marking_values.iloc[index]) else ' '

                    level_value = level_values.iloc[index] if pd.notna(level_values.iloc[index]) else ' '

                    PartDesk.objects.create(
                        applicatorNumber=applicator_part,
                        partName=part_name,  # Gunakan PartName yang sesuai dengan kolom saat ini
                        partNumber=part_number_value,
                        partCode=part_code_value,
                        level=level_value,
                        marking=marking_value
                    )

                # Pindah ke kolom berikutnya
                col_index += step

            return redirect('applicator')
    else:
        form = UploadFileForm()

    applicator_parts = ApplicatorPart.objects.all().order_by('id')
    part_names = PartName.objects.all().order_by('id')
    part_desks = PartDesk.objects.all().order_by('id')

    return render(request, 'applicator.html', {
        'form': form,
        'applicator_parts': applicator_parts,
        'part_names': part_names,
        'part_desks': part_desks,
    })

@login_required()  
def reset_applicator(request):
    PartDesk.objects.all().delete()
    PartName.objects.all().delete()
    ApplicatorPart.objects.all().delete()
    return redirect('applicator')

# Stroke Part
@login_required
def strokePart(request):
    applicators = Load_applicator.objects.all()

    # ----- ADD -----
    if request.method == 'POST' and 'add' in request.POST:
        name = request.POST['name']
        loading = request.POST['loading']
        image = request.FILES.get('image')
        Load_applicator.objects.create(name=name, loading=loading, image=image)
        return redirect(reverse('strokePart'))

    # ----- EDIT -----
    if request.method == 'POST' and 'edit' in request.POST:
        applicator_id = request.POST['applicator_id']
        applicator = get_object_or_404(Load_applicator, id=applicator_id)
        applicator.name = request.POST['name']
        applicator.loading = request.POST['loading']
        if 'image' in request.FILES:
            applicator.image = request.FILES['image']
        applicator.save()
        return redirect(reverse('strokePart'))

    if request.method == 'POST' and 'delete' in request.POST:
        applicator_id = request.POST['applicator_id']
        applicator = get_object_or_404(Load_applicator, id=applicator_id)

        # Pastikan semuanya di‑hapus dalam satu transaksi
        with transaction.atomic():
            # Hapus semua baris LoadingPartResult yang part_name‑nya sama
            LoadingPartResult.objects.filter(
                part_name__iexact=applicator.name   # abaikan besar‑kecil huruf
            ).delete()
            # Hapus stroke part‑nya sendiri
            applicator.delete()

        return redirect(reverse('strokePart'))

    return render(request, 'strokePart.html', {'applicators': applicators})

#  about us
@login_required()
def about(request):
    return render(request, 'aboutEMRP.html')
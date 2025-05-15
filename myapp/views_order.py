from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from myapp.models import Departement, Section

def master_departement_section(request):
    departements = Departement.objects.all()
    sections = Section.objects.select_related('departement').all()
    return render(request, 'departement/departement.html', {
        'departements': departements,
        'sections': sections,
    })


def create_departement(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Departement.objects.create(name=name)
            messages.success(request, 'Departement berhasil ditambahkan.')
        else:
            messages.error(request, 'Nama Departement tidak boleh kosong.')
    return redirect('master_departement_section')

def create_section(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        departement_id = request.POST.get('departement')
        if name and departement_id:
            departement = Departement.objects.get(id=departement_id)
            Section.objects.create(name=name, departement=departement)
            messages.success(request, 'Section berhasil ditambahkan.')
        else:
            messages.error(request, 'Semua field Section harus diisi.')
    return redirect('master_departement_section')

# purchase request
from django.db.models import Avg
from .form import PurchaseRequestForm
from .models import LoadingPartResult
from .models import PurchaseRequest

@login_required
def purchaseReq(request):
    purchase_requests = PurchaseRequest.objects.all().order_by('-date')  # Ambil semua PR terbaru

    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST)
        if form.is_valid():
            pr = form.save(commit=False)
            carlines = form.cleaned_data['part_order']

            total_amount = 0
            amount = 0

            for carline in carlines:
                loading_parts = LoadingPartResult.objects.filter(carline=carline)
                avg = loading_parts.aggregate(Avg('average_round'))['average_round__avg'] or 0
                part_amount = int(avg * pr.estimated_price)
                total_amount += part_amount
                amount += part_amount

            pr.amount = amount
            pr.total_amount = total_amount
            pr.save()
            pr.part_order.set(carlines)
            return redirect('purchaseReq')
        else:
            print(form.errors)
    else:
        form = PurchaseRequestForm()

    return render(request, 'order/purchaseReq.html', {
        'form': form,
        'purchase_requests': purchase_requests
    })

# purchase order
@login_required()
def purchaseOrd(request):
    return render(request, 'order/purchaseOrd.html')

# schedule confirmation
@login_required()
def scheduleConf(request):
    return render(request, 'order/scheduleConf.html')

# Airway bill
@login_required()
def airwayBill(request):
    return render(request, 'order/airwayBill.html')

# invoice
@login_required()
def invoice(request):
    return render(request, 'order/invoice.html')
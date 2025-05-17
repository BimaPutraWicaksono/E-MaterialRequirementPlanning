from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from myapp.models import Departement, Section

@login_required()
def master_departement_section(request):
    departements = Departement.objects.all()
    sections = Section.objects.select_related('departement').all()
    return render(request, 'departement/departement.html', {
        'departements': departements,
        'sections': sections,
    })

@login_required()
def create_departement(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Departement.objects.create(name=name)
            messages.success(request, 'Departement berhasil ditambahkan.')
        else:
            messages.error(request, 'Nama Departement tidak boleh kosong.')
    return redirect('master_departement_section')

@login_required()
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

from django.shortcuts import render, redirect
from .models import PurchaseRequest, LoadingPartResult, RequestForm, RequestItem
from .form import PurchaseRequestForm
from django.http import JsonResponse
from django.template.loader import render_to_string

from django.shortcuts import render, redirect
from .models import PurchaseRequest, LoadingPartResult, RequestForm, RequestItem
from .form import PurchaseRequestForm
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

@login_required()
def purchaseReq(request):
    loading_parts = []

    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST)
        if form.is_valid():
            selected_carlines = form.cleaned_data['part_order']
            budget_ref_no = request.POST.getlist('budget_ref_no')
            estimated_prices = request.POST.getlist('estimated_price')
            deadlines = request.POST.getlist('deadline')
            total_amount_hidden = request.POST.get('total_amount_hidden')

            try:
                total_amount = float(total_amount_hidden)
            except (TypeError, ValueError):
                total_amount = 0

            pr = form.save(commit=False)
            pr.amount = total_amount
            pr.total_amount = total_amount
            pr.save()
            pr.part_order.set(selected_carlines)

            rf = RequestForm.objects.create(
                date=pr.date,
                registered_no=pr.registered_no,
                section=pr.section.name,
                purchase_by=pr.purchase_by,
                requested=pr.requested,
                total_amount=total_amount
            )
            rf.carlines.set(selected_carlines)

            index = 0
            for carline in selected_carlines:
                parts = LoadingPartResult.objects.filter(carline=carline)
                for part in parts:
                    try:
                        budget = budget_ref_no[index]
                        est_price = float(estimated_prices[index])
                        dl = deadlines[index]
                    except (IndexError, ValueError):
                        budget = ""
                        est_price = 0
                        dl = ""

                    result_avg = part.average_round or 0
                    amount = result_avg * est_price

                    RequestItem.objects.create(
                        request_form=rf,
                        loading_part_result=part,
                        budget_ref_no=budget,
                        result_average_round=result_avg,
                        estimated_price=est_price,
                        amount=amount,
                        deadline=dl
                    )

                    index += 1

            return redirect('purchaseReq')
    else:
        form = PurchaseRequestForm()

    return render(request, 'order/purchaseReq.html', {
        'form': form,
        'loading_parts': loading_parts,
    })

@login_required()
def ajax_get_loading_parts(request):
    if request.method == 'POST':
        carline_ids = request.POST.getlist('carline_ids[]')
        loading_parts = LoadingPartResult.objects.filter(carline__id__in=carline_ids)
        table_html = render_to_string('partials/loading_parts_table.html', {
            'loading_parts': loading_parts
        })
        return JsonResponse({'table': table_html})


from django.shortcuts import render, redirect
from .form import RequestFormForm
from .models import RequestForm, RequestItem, LoadingPartResult, Carline
@login_required()
def create_request_form(request):
    if request.method == 'POST':
        form = RequestFormForm(request.POST)
        if form.is_valid():
            request_form = form.save()
            selected_carlines = form.cleaned_data['carlines']
            for carline in selected_carlines:
                parts = LoadingPartResult.objects.filter(carline=carline)
                for part in parts:
                    item = RequestItem.objects.create(
                        request_form=request_form,
                        loading_part_result=part,
                        budget_ref_no='manual',  # default
                        result_average_round=0,  # user edit manual setelah submit
                        estimated_price=0,       # user edit manual setelah submit
                        amount=0,
                        deadline='isi sendiri',
                    )
            return redirect('request_success')
    else:
        form = RequestFormForm()
        selected_carlines = request.GET.getlist('carlines')
        carlines = Carline.objects.all()
        parts_per_carline = {}
        for carline in carlines:
            parts_per_carline[carline] = LoadingPartResult.objects.filter(carline=carline)
        return render(request, 'order/purchaseOrd.html', {
            'form': form,
            'parts_per_carline': parts_per_carline
        })

    return render(request, 'order/purchaseOrd.html', {'form': form})
 
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
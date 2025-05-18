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
# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import PurchaseRequest, RequestItem, LoadingPartResult
from .form import PurchaseRequestForm

@login_required
def purchaseReq(request):
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
            pr.total_amount = total_amount

            # Approval logic
            action = request.POST.get('action')

            if request.user.groups.filter(name="Supervisor").exists():
                if action == 'approve_spv':
                    pr.approve_spv = True
                elif action == 'disapprove_spv':
                    pr.approve_spv = False

            if request.user.groups.filter(name="Senior Supervisor").exists():
                if action == 'approve_sspv':
                    pr.approve_sspv = True
                elif action == 'disapprove_sspv':
                    pr.approve_sspv = False


            pr.save()
            pr.part_order.set(selected_carlines)

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
                        dl = None

                    avg = part.average_round or 0
                    amount = avg * est_price

                    RequestItem.objects.create(
                        purchase_request=pr,
                        loading_part_result=part,
                        budget_ref_no=budget,
                        result_average_round=avg,
                        estimated_price=est_price,
                        amount=amount,
                        deadline=dl
                    )
                    index += 1

                messages.success(request, "Purchase Request berhasil dikirim.")
                
            return redirect('purchaseReq')
    else:
        form = PurchaseRequestForm()

    return render(request, 'order/purchaseReq.html', {
        'form': form,
    })

@login_required
def ajax_get_loading_parts(request):
    if request.method == 'POST':
        carline_ids = request.POST.getlist('carline_ids[]')
        loading_parts = LoadingPartResult.objects.filter(carline__id__in=carline_ids)
        table_html = render_to_string('partials/loading_parts_table.html', {
            'loading_parts': loading_parts
        })
        return JsonResponse({'table': table_html})

@login_required
def ajax_load_sections(request):
    departement_id = request.GET.get('departement_id')
    sections = Section.objects.filter(departement_id=departement_id).order_by('name')
    html = render_to_string('partials/section_dropdown_list_options.html', {'sections': sections})
    return JsonResponse(html, safe=False)


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
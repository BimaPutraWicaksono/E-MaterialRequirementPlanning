from django.shortcuts import render, redirect, get_object_or_404
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

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import PurchaseRequest, RequestItem, LoadingPartResult, Carline, Section
from .form import PurchaseRequestForm
from django.db.models import Q

@login_required
def purchaseReq(request):
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST)
        if form.is_valid():
            selected_carlines = form.cleaned_data['part_order']
            budget_ref_no_list = request.POST.getlist('budget_ref_no')
            estimated_prices_list = request.POST.getlist('estimated_price')
            deadlines_list = request.POST.getlist('deadline')
            total_amount_hidden = request.POST.get('total_amount_hidden')

            try:
                total_amount = float(total_amount_hidden)
            except (TypeError, ValueError):
                total_amount = 0

            pr = form.save(commit=False)
            pr.total_amount = total_amount
            pr.save()
            pr.part_order.set(selected_carlines)

            pr.items.all().delete()

            all_parts = []
            seen_partdesk_ids = set()

            for carline in selected_carlines:
                parts = LoadingPartResult.objects.filter(carline=carline).order_by('partdesk')
                for part in parts:
                    if part.partdesk_id and part.partdesk_id not in seen_partdesk_ids:
                        seen_partdesk_ids.add(part.partdesk_id)
                        all_parts.append(part)

            for i, part in enumerate(all_parts):
                try:
                    budget = budget_ref_no_list[i]
                    est_price = float(estimated_prices_list[i])
                    dl = deadlines_list[i] if deadlines_list[i] else None
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

            messages.success(request, "Purchase Request berhasil disimpan.")
            return redirect('purchaseReq')
    else:
        form = PurchaseRequestForm()

    # Filter berdasarkan query parameter
    if 'filter' in request.GET:
        filter_option = request.GET['filter']
    else:
        if request.user.groups.filter(name='Karyawan').exists():
            filter_option = 'all'
        elif request.user.groups.filter(name='Supervisor').exists():
            filter_option = 'pending'
        else:
            filter_option = 'all'  # fallback

    requests = PurchaseRequest.objects.all()

    # Tambahkan logika filter baru
    if filter_option == 'pending':
        requests = requests.filter(
            approve_spv__isnull=True
        )
    elif filter_option == 'approved_spv':
        requests = requests.filter(
            approve_spv=True
        )
    elif filter_option == 'rejected':
        requests = requests.filter(
            Q(approve_spv=False)
        )

    requests = requests.order_by('-date')

    return render(request, 'order/purchaseReq.html', {
        'form': form,
        'requests': requests,
        'filter_option': filter_option,
    })

@login_required
def ajax_get_loading_parts(request):
    if request.method == 'POST':
        carline_ids = request.POST.getlist('carline_ids[]')
        parts = LoadingPartResult.objects.filter(carline__id__in=carline_ids).order_by('partdesk')

        unique_parts = {}
        for part in parts:
            if part.partdesk_id not in unique_parts:
                unique_parts[part.partdesk_id] = part
        
        parts_list = unique_parts.values()

        table_html = render_to_string('partials/loading_parts_table.html', {
            'parts': parts_list
        })
        return JsonResponse({'table': table_html})

@login_required
def ajax_load_sections(request):
    departement_id = request.GET.get('departement_id')
    sections = Section.objects.filter(departement_id=departement_id).order_by('name')
    html = render_to_string('partials/section_dropdown_list_options.html', {'sections': sections})
    return JsonResponse(html, safe=False)


@login_required
def purchase_request_detail(request, registered_no):
    pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)
    items = RequestItem.objects.filter(purchase_request=pr)

    context = {
        'purchase_request': pr,
        'request_items': items,
    }

    # Render template ke string
    html = render_to_string('partials/purchase_request_detail.html', context, request=request)
    return JsonResponse({'html': html})


@login_required
def approve_purchase_request(request, registered_no):
    pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Supervisor
        if request.user.groups.filter(name='Supervisor').exists():
            if action == 'approve_spv':
                pr.approve_spv = True
                pr.reason_spv = ''
            elif action == 'disapprove_spv':
                reason = request.POST.get('reason_spv', '').strip()
                if not reason:
                    messages.error(request, "Alasan penolakan harus diisi oleh Supervisor.")
                    return redirect(request.META.get('HTTP_REFERER'))
                pr.approve_spv = False
                pr.reason_spv = reason
            pr.save()
            messages.success(request, "Supervisor approval updated.")
        return redirect('purchaseReq')

from django.shortcuts import get_object_or_404, redirect
from .models import PurchaseRequest

def delete_purchase_request(request, registered_no):
    if request.method == "POST":
        pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)
        pr.delete()
        messages.success(request, f"Purchase Request {registered_no} berhasil dihapus.")
    return redirect('purchaseReq')  # ganti sesuai nama path untuk halaman PR utama

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import RequestItem
from .form import PurchaseRequestForm, PurchaseRequestEditForm

def purchase_request_edit(request, registered_no):
    pr = get_object_or_404(PurchaseRequest, registered_no=registered_no)

    if request.method == 'POST':
        form = PurchaseRequestEditForm(request.POST, instance=pr)
        if form.is_valid():
            form.save()

            # Tangkap data item
            estimated_prices = request.POST.getlist('estimated_price')
            budget_ref_nos = request.POST.getlist('budget_ref_no')
            deadlines = request.POST.getlist('deadline')
            item_ids = request.POST.getlist('item_id')

            total_amount = 0
            for i, item_id in enumerate(item_ids):
                if not item_id.strip():  # skip if empty or whitespace
                    continue
                try:
                    item = RequestItem.objects.get(id=item_id, purchase_request=pr)
                except RequestItem.DoesNotExist:
                    continue

                # Update nilai
                try:
                    est_price = float(estimated_prices[i])
                except (ValueError, IndexError):
                    est_price = 0

                budget = budget_ref_nos[i] if i < len(budget_ref_nos) else ""
                deadline = deadlines[i] if i < len(deadlines) and deadlines[i] else None

                avg = item.result_average_round or 0
                amount = avg * est_price

                # Update item
                item.estimated_price = est_price
                item.budget_ref_no = budget
                item.deadline = deadline
                item.amount = amount
                item.save()

                total_amount += amount

            pr.total_amount = total_amount
            pr.save()

            return redirect('purchaseReq')
    else:
        form = PurchaseRequestEditForm(instance=pr)

    context = {
        'form': form,
        'registered_no': registered_no,
        'purchase_request': pr,
    }
    return render(request, 'order/purchase_request_edit.html', context)

@login_required
def ajax_get_loading_parts_edit(request):
    if request.method == 'POST':
        carline_ids = request.POST.getlist('carline_ids')
        purchase_request_id = request.POST.get('purchase_request_id')
        parts = LoadingPartResult.objects.filter(carline__id__in=carline_ids).order_by('partdesk')

        unique_parts = {}
        for part in parts:
            if part.partdesk_id not in unique_parts:
                unique_parts[part.partdesk_id] = part
        
        parts_list = unique_parts.values()

        existing_details = {}
        if purchase_request_id:
            details_qs = RequestItem.objects.filter(purchase_request_id=purchase_request_id)
            for d in details_qs:
                existing_details[d.loading_part_result.partdesk_id] = d

        table_html = render_to_string('partials/loading_parts_table_edit.html', {
            'parts': parts_list,
            'existing_details': existing_details
        })
        return JsonResponse({'table': table_html})

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